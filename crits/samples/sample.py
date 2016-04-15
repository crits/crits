from mongoengine import Document
from mongoengine import StringField, ListField
from mongoengine import IntField
from django.conf import settings

from crits.samples.migrate import migrate_sample
from crits.core.crits_mongoengine import CritsBaseAttributes
from crits.core.crits_mongoengine import CritsSourceDocument
from crits.core.crits_mongoengine import CritsActionsDocument
from crits.core.fields import getFileField


class Sample(CritsBaseAttributes, CritsSourceDocument, CritsActionsDocument,
             Document):
    """Sample object"""

    meta = {
        "collection": settings.COL_SAMPLES,
        "crits_type": 'Sample',
        "latest_schema_version": 4,
        "shard_key": ('md5',),
        "schema_doc": {
            'filename': 'The name of the last file that was uploaded with this'\
                'MD5',
            'filenames': 'A list of filenames this binary has gone by.',
            'filetype': 'The filetype of the file',
            'mimetype': 'The mimetype of the file',
            'size': 'The size of the file',
            'md5': 'The MD5 of the file',
            'sha1': 'The SHA1 of the file',
            'sha256': 'The SHA256 of the file',
            'ssdeep': 'The ssdeep of the file',
            'campaign': 'List [] of campaigns using this file',
            'source': 'List [] of sources that provided this file',
            'created': 'ISODate of when this file was uploaded',
            'modified': 'ISODate of when the file metadata was last modified',
            'filedata': 'The ObjectId of the file in GridFS'
        },
        "jtable_opts": {
                         'details_url': 'crits.samples.views.detail',
                         'details_url_key': 'md5',
                         'default_sort': "created DESC",
                         'searchurl': 'crits.samples.views.samples_listing',
                         'fields': [ "filename", "size", "filetype",
                                     "created", "modified", "campaign",
                                     "source", "md5", "id", "status"],
                         'jtopts_fields': [ "details",
                                            "filename",
                                            "size",
                                            "filetype",
                                            "created",
                                            "campaign",
                                            "source",
                                            "md5",
                                            "status",
                                            "favorite",
                                            "id"],
                         'hidden_fields': ["md5"],
                         'linked_fields': ["filename", "source", "campaign",
                                           "filetype"],
                         'details_link': 'details',
                         'no_sort': ['details', 'id']
                       },
    }

    filedata = getFileField(collection_name=settings.COL_SAMPLES)
    filename = StringField(required=True)
    filenames = ListField(StringField())
    filetype = StringField()
    md5 = StringField(required=True)
    mimetype = StringField()
    sha1 = StringField()
    sha256 = StringField()
    size = IntField(default=0)
    ssdeep = StringField()

    def migrate(self):
        migrate_sample(self)

    def add_file_data(self, file_data):
        self._generate_file_metadata(file_data)
        self.filedata = file_data

    def add_file_obj(self, file_obj):
        data = file_obj.read()
        self._generate_file_metadata(data)
        self.filedata = data

    def _generate_file_metadata(self, data):
        import pydeep
        import magic
        from hashlib import md5, sha1, sha256
        try:
            self.filetype = magic.from_buffer(data)
        except:
            self.filetype = "Unavailable"
        try:
            mimetype = magic.from_buffer(data, mime=True)
            if mimetype:
                self.mimetype = mimetype.split(";")[0]
            if not mimetype:
                self.mimetype = "unknown"
        except:
            self.mimetype = "Unavailable"
        self.size = len(data)
        # this is a shard key. you can't modify it once it's set.
        # MongoEngine will still mark the field as modified even if you set it
        # to the same value.
        if not self.md5:
            self.md5 = md5(data).hexdigest()
        self.sha1 = sha1(data).hexdigest()
        self.sha256 = sha256(data).hexdigest()
        try:
            self.ssdeep = pydeep.hash_bytes(data)
        except:
            self.ssdeep = None

    def is_pe(self):
        """
        Is this a PE file.
        """

        return self.filedata.grid_id != None and self.filedata.read(2) == "MZ"

    def is_pdf(self):
        """
        Is this a PDF.
        """

        return self.filedata.grid_id != None and "%PDF-" in self.filedata.read(1024)

    def discover_binary(self):
        """
            Queries GridFS for a matching binary to this sample document.
        """

        from crits.core.mongo_tools import mongo_connector

        fm = mongo_connector("%s.files" % self._meta['collection'])
        objectid = fm.find_one({'md5': self.md5}, {'_id': 1})
        if objectid:
            self.filedata.grid_id = objectid['_id']
            self.filedata._mark_as_changed()

    def set_filenames(self, filenames):
        """
        Set the Sample filenames to a specified list.

        :param filenames: The filenames to set.
        :type filenames: list

        """

        if isinstance(filenames, list):
            self.filenames = filenames
