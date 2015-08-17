import datetime

from dateutil.parser import parse
from mongoengine import DateTimeField, FileField
from mongoengine.connection import DEFAULT_CONNECTION_NAME
from mongoengine.python_support import str_types
import io

from django.conf import settings
if settings.FILE_DB == settings.S3:
    import crits.core.s3_tools as S3

class CritsDateTimeField(DateTimeField):
    """
    Custom MongoEngine DateTimeField. Utilizes a transform such that if the
    value passed in is a string we will convert it to a datetime.datetime
    object, or if it is set to None we will use the current datetime (useful
    when instantiating new objects and wanting the default dates to all be the
    current datetime).
    """

    def __set__(self, instance, value):
        value = self.transform(value)
        return super(CritsDateTimeField, self).__set__(instance, value)

    def transform(self, value):
        if value and isinstance(value, basestring):
            return parse(value, fuzzy=True)
        elif not value:
            return datetime.datetime.now()
        else:
            return value

class S3Proxy(object):
    """
    Custom proxy for MongoEngine which uses S3 to store binaries instead of
    GridFS.
    """

    def __init__(self, grid_id=None, key=None, instance=None,
                 db_alias=DEFAULT_CONNECTION_NAME, collection_name='fs'):
        self.grid_id = grid_id # Store id for file
        self.key = key
        self.instance = instance
        self.db_alias = db_alias
        self.collection_name = collection_name
        self.newfile = None # Used for partial writes
        self.gridout = None

    def __getattr__(self, name):
        attrs = ('_fs', 'grid_id', 'key', 'instance', 'db_alias',
                 'collection_name', 'newfile', 'gridout')
        if name in attrs:
            return self.__getattribute__(name)
        obj = self.get()
        if name in dir(obj):
            return getattr(obj, name)
        raise AttributeError

    def __get__(self, instance, value):
        return self

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.grid_id)

    def delete(self):
        # Delete file from S3, FileField still remains
        S3.delete_file_s3(self.grid_id,self.collection_name)
        self.grid_id = None
        self.gridout = None
        self._mark_as_changed()

    def get(self, id=None):
        if id:
            self.grid_id = id
        if self.grid_id is None:
            return None

        try:
            if self.gridout is None:
                self.gridout = io.BytesIO(S3.get_file_s3(self.grid_id, self.collection_name))
            return self.gridout
        except:
            return None

    def put(self, file_obj, **kwargs):
        if self.grid_id:
            raise Exception('This document already has a file. Either delete '
                              'it or call replace to overwrite it')

        self.grid_id = S3.put_file_s3(file_obj, self.collection_name)
        self._mark_as_changed()

    def read(self, size=-1):
        gridout = self.get()
        if gridout is None:
            return None
        else:
            try:
                return gridout.read(size)
            except:
                return ""

    def _mark_as_changed(self):
        """Inform the instance that `self.key` has been changed"""
        if self.instance:
            self.instance._mark_as_changed(self.key)

class S3FileField(FileField):
    """
    Custom FileField for MongoEngine which utilizes S3.
    """

    def __init__(self, db_alias=DEFAULT_CONNECTION_NAME, collection_name="fs",
                 **kwargs):
        super(S3FileField, self).__init__(db_alias, collection_name, **kwargs)
        self.proxy_class = S3Proxy

    def __set__(self, instance, value):
        key = self.name
        if ((hasattr(value, 'read') and not
             isinstance(value, self.proxy_class)) or isinstance(value, str_types)):
            # using "FileField() = file/string" notation
            grid_file = instance._data.get(self.name)
            # If a file already exists, delete it
            if grid_file:
                try:
                    grid_file.delete()
                except:
                    pass
                # Create a new file with the new data
                grid_file.put(value)
            else:
                # Create a new proxy object as we don't already have one
                instance._data[key] = self.proxy_class(key=key, instance=instance,
                                                       collection_name=self.collection_name)
                instance._data[key].put(value)
        else:
            instance._data[key] = value

        instance._mark_as_changed(key)


def getFileField(db_alias=DEFAULT_CONNECTION_NAME, collection_name="fs", **kwargs):
    """
    Determine if the admin has configured CRITs to utilize GridFS or S3 for
    binary storage.
    """

    if settings.FILE_DB == settings.GRIDFS:
        return FileField(db_alias, collection_name, **kwargs)
    elif settings.FILE_DB == settings.S3:
        return S3FileField(db_alias, collection_name, **kwargs)
