import datetime
import json, yaml
import io
import csv

from bson import json_util, ObjectId
from collections import OrderedDict
from dateutil.parser import parse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from mongoengine import Document, EmbeddedDocument, DynamicEmbeddedDocument
from mongoengine import StringField, ListField, EmbeddedDocumentField
from mongoengine import IntField, DateTimeField, ObjectIdField, BooleanField
from mongoengine.base import BaseDocument, ValidationError

# Determine if we should be caching queries or not.
from mongoengine import QuerySet as QS

from pprint import pformat

from crits.core.user_tools import user_sources, get_user_info, get_user_role
from crits.core.fields import CritsDateTimeField
from crits.core.class_mapper import class_from_id, class_from_type
from crits.vocabulary.relationships import RelationshipTypes
from crits.vocabulary.objects import ObjectTypes

# Hack to fix an issue with non-cached querysets and django-tastypie-mongoengine
# The issue is in django-tastypie-mongoengine in resources.py from what I can
# tell.
try:
    from mongoengine.queryset import tranform as mongoengine_tranform
except ImportError:
    mongoengine_tranform = None

QUERY_TERMS_ALL = getattr(mongoengine_tranform, 'MATCH_OPERATORS', (
    'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'nin', 'mod', 'all', 'size', 'exists',
    'not', 'within_distance', 'within_spherical_distance', 'within_box',
    'within_polygon', 'near', 'near_sphere', 'contains', 'icontains',
    'startswith', 'istartswith', 'endswith', 'iendswith', 'exact', 'iexact',
    'match'
))

class Query(object):
    """
    Query class to hold available query terms.
    """

    query_terms = dict([(query_term, None) for query_term in QUERY_TERMS_ALL])

class CritsQuerySet(QS):
    """
    CRITs default QuerySet. Used to override methods like .only() and to extend
    it with other methods we want to perform on a QuerySet object.
    """

    _len = None
    query = Query()

    def __len__(self):
        """
        Modified version of the default __len__() which allows
        us to get the length with or without caching enabled.
        """

        if self._len is not None:
            return self._len
        if self._has_more:
            # populate the cache
            list(self._iter_results())
            self._len = len(self._result_cache)
        else:
            self._len = self.count()
        return self._len

    def only(self, *fields):
        """
        Modified version of the default only() which allows
        us to add default fields we always want to include.
        """

        #Always include schema_version so we can migrate if needed.
        if 'schema_version' not in fields:
            fields = fields + ('schema_version',)
        return super(CritsQuerySet, self).only(*fields)

    def from_json(self, json_data):
        """
        Converts JSON data to unsaved objects.

        Takes either a Python list of individual JSON objects or the
        result of calling json.dumps on a Python list of Python
        dictionaries.

        :param json_data: List or result of json.dumps.
        :type json_data: list or str
        :returns: :class:`crits.core.crits_mongoengine.CritsQuerySet`
        """

        if not isinstance(json_data, list):
            son_data = json_util.loads(json_data)
            return [self._document._from_son(data) for data in son_data]
        else:
            #Python list of JSON objects
            return [self._document.from_json(data) for data in json_data]

    def to_dict(self, excludes=[], projection=[]):
        """
        Converts CritsQuerySet to a list of dictionaries.

        :param excludes: List fields to exclude in each document.
        :type excludes: list
        :param projection: List fields to limit results on.
        :type projectsion: list
        :returns: list of dictionaries
        """

        return [obj.to_dict(excludes,projection) for obj in self]

    def to_csv(self, fields):
        """
        Converts CritsQuerySet to CSV formatted string.

        :param fields: List fields to return for each document.
        :type fields: list
        :returns: str
        """

        filter_keys = [
                       'id',
                       'password',
                       'password_reset',
                       'schema_version',
                       ]
        if not fields:
            fields = self[0]._data.keys()
        # Create a local copy
        fields = fields[:]
        for key in filter_keys:
            if key in fields:
                fields.remove(key)
        csvout = ",".join(fields) + "\n"
        csvout += "".join(obj.to_csv(fields) for obj in self)
        return csvout

    def to_json(self, exclude=[]):
        """
        Converts a CritsQuerySet to JSON.

        :param exclude: Fields to exclude from each document.
        :type exclude: list
        :returns: json
        """

        return json.dumps([obj.to_dict(exclude) for obj in self],
            default=json_handler)

    def from_yaml(self, yaml_data):
        """
        Converts YAML data to a list of unsaved objects.

        :param yaml_data: The YAML to convert.
        :type yaml_data: list
        :returns: list
        """

        return [self._document.from_yaml(doc) for doc in yaml_data]

    def to_yaml(self, exclude=[]):
        """
        Converts a CritsQuerySet to a list of YAML docs.

        :param exclude: Fields to exclude from each document.
        :type exclude: list
        :returns: list
        """

        return [doc.to_yaml(exclude) for doc in self]

    def sanitize_sources(self, username=None):
        """
        Sanitize each document in a CritsQuerySet for source information and
        return the results as a list.

        :param username: The user which requested the data.
        :type username: str
        :returns: list
        """

        if not username:
            return self
        sources = user_sources(username)
        final_list = []
        for doc in self:
            doc.sanitize_sources(username, sources)
            final_list.append(doc)
        return final_list

    def sanitize_source_tlps(self, user=None):
        """
        Sanitize the results of a query so that the user is only shown results
        that they have the source and TLP permission to view.

        :param username: The user which requested the data.
        :type username: str
        :returns: CritsQuerySet
        """

        if not user:
            return self

        filterlist = []

        for doc in self:
            if user.check_source_tlp(doc):
                filterlist.append(doc.id)

        return self.filter(id__in=filterlist)

class CritsDocumentFormatter(object):
    """
    Class to inherit from to gain the ability to convert a top-level object
    class to another format.
    """

    def to_json(self):
        """
        Return the object in JSON format.
        """

        return self.to_mongo()

    def to_dict(self):
        """
        Return the object as a dict.
        """

        return self.to_mongo().to_dict()

    def __str__(self):
        """
        Allow us to use `print`.
        """

        return self.to_json()

    def merge(self, arg_dict=None, overwrite=False, **kwargs):
        """
        Merge a dictionary into a top-level object class.

        :param arg_dict: The dictionary to get data from.
        :type arg_dict: dict
        :param overwrite: Whether or not to overwrite data in the object.
        :type overwrite: boolean
        """

        merge(self, arg_dict=arg_dict, overwrite=overwrite)


class CritsStatusDocument(BaseDocument):
    """
    Inherit to add status to a top-level object.
    """

    status = StringField(default="New")

    def set_status(self, status):
        """
        Set the status of a top-level object.

        :param status: The status to set:
                       ('New', 'In Progress', 'Analyzed', Deprecated')
        """

        if status in ('New', 'In Progress', 'Analyzed', 'Deprecated'):
            self.status = status
            if status == 'Deprecated' and 'actions' in self:
                for action in self.actions:
                    action.active = "off"

class CritsBaseDocument(BaseDocument):
    """
    Inherit to add a created and modified date to a top-level object.
    """

    created = CritsDateTimeField(default=datetime.datetime.now)
    # modified will be overwritten on save
    modified = CritsDateTimeField()


class CritsSchemaDocument(BaseDocument):
    """
    Inherit to add a schema_version to a top-level object.

    Default schema_version is 0 so that later, on .save(), we can tell if a
    document coming from the DB never had a schema_version assigned and
    raise an error.
    """

    schema_version = IntField(default=0)


class UnsupportedAttrs(DynamicEmbeddedDocument, CritsDocumentFormatter):
    """
    Inherit to allow a top-level object to store unsupported attributes.
    """

    meta = {}


class CritsDocument(BaseDocument):
    """
    Mixin for adding CRITs specific functionality to the MongoEngine module.

    All CRITs MongoEngine-based classes should inherit from this class
    in addition to MongoEngine's Document.

    NOTE: this class uses some undocumented methods and attributes from MongoEngine's
    BaseDocument and may need to be revisited if/when the code is updated.
    """

    meta = {
        'duplicate_attrs':[],
        'migrated': False,
        'migrating': False,
        'needs_migration': False,
        'queryset_class': CritsQuerySet
    }

    unsupported_attrs = EmbeddedDocumentField(UnsupportedAttrs)

    def __init__(self, **values):
        """
        Override .save() and .delete() with our own custom versions.
        """

        if hasattr(self, 'save'):
            #.save() is normally defined on a Document, not BaseDocument, so
            #   we'll have to monkey patch to call our save.
            self.save = self._custom_save
        if hasattr(self, 'delete'):
            #.delete() is normally defined on a Document, not BaseDocument, so
            #   we'll have to monkey patch to call our delete.
            self.delete = self._custom_delete
        self._meta['strict'] = False
        super(CritsDocument, self).__init__(**values)

    def _custom_save(self, force_insert=False, validate=True, clean=False,
        write_concern=None,  cascade=None, cascade_kwargs=None,
        _refs=None, username=None, **kwargs):
        """
        Custom save function. Extended to check for valid schema versions,
        automatically update modified times, and audit the changes made.
        """

        from crits.core.handlers import audit_entry
        if hasattr(self, 'schema_version') and not self.schema_version:
            #Check that documents retrieved from the DB have a recognized
            #   schema_version
            if not self._created:
                raise UnrecognizedSchemaError(self)
            #If it's a new document, set the appropriate schema version
            elif hasattr(self, '_meta') and 'latest_schema_version' in self._meta:
                self.schema_version = self._meta['latest_schema_version']
        #TODO: convert this to using UTC
        if hasattr(self, 'modified'):
            self.modified = datetime.datetime.now()
        do_audit = False
        if self.id:
            audit_entry(self, username, "save")
        else:
            do_audit = True

        # MongoEngine evidently tries to add partial functions as attributes:
        # https://github.com/MongoEngine/mongoengine/blob/master/mongoengine/base/document.py#L967
        # A bit of a hack but removing it manually until we can figure out why it is
        # here and how to stop it from happening.
        try:
            self.unsupported_attrs.__delattr__('get_tlp_display')
        except:
            pass

        super(self.__class__, self).save(force_insert=force_insert,
                                         validate=validate,
                                         clean=clean,
                                         write_concern=write_concern,
                                         cascade=cascade,
                                         cascade_kwargs=cascade_kwargs,
                                         _refs=_refs)
        if do_audit:
            audit_entry(self, username, "save", new_doc=True)
        return

    def _custom_delete(self, username=None, **write_concern):
        """
        Custom delete function. Overridden to allow us to extend to other parts
        of CRITs and clean up dangling relationships, comments, objects, GridFS
        files, bucket_list counts, and favorites.
        """

        from crits.core.handlers import audit_entry, alter_bucket_list
        audit_entry(self, username, "delete")
        if self._has_method("delete_all_relationships"):
            self.delete_all_relationships(username=username)
        if self._has_method("delete_all_comments"):
            self.delete_all_comments()
        if self._has_method("delete_all_analysis_results"):
            self.delete_all_analysis_results()
        if self._has_method("delete_all_objects"):
            self.delete_all_objects()
        if self._has_method("delete_all_favorites"):
            self.delete_all_favorites()
        if hasattr(self, 'filedata'):
            self.filedata.delete()
        if hasattr(self, 'bucket_list'):
            alter_bucket_list(self, self.bucket_list, -1)
        super(self.__class__, self).delete()
        return

    def __setattr__(self, name, value):
        """
        Overriden to handle unsupported attributes.
        """

        #Make sure name is a valid field for MongoDB. Also, name cannot begin with
        #   underscore because that indicates a private MongoEngine attribute.
        if (not self._dynamic and hasattr(self, 'unsupported_attrs')
            and not name in self._fields and not name.startswith('_')
            and not name.startswith('$') and not '.' in name
            and name not in ('save', 'delete')):
            if not self.unsupported_attrs:
                self.unsupported_attrs = UnsupportedAttrs()
            self.unsupported_attrs.__setattr__(name, value)
        else:
            super(CritsDocument, self).__setattr__(name, value)

    def _has_method(self, method):
        """
        Convenience method for determining if a method exists for this class.

        :param method: The method to check for.
        :type method: str
        :returns: True, False
        """

        if hasattr(self, method) and callable(getattr(self, method)):
            return True
        else:
            return False

    @classmethod
    def _from_son(cls, son, _auto_dereference=True, only_fields=None, created=False):
        """
        Override the default _from_son(). Allows us to move attributes in the
        database to unsupported_attrs if needed, validate the schema_version,
        and automatically migrate to newer schema versions.
        """

        doc = super(CritsDocument, cls)._from_son(son, _auto_dereference)
        #Make sure any fields that are unsupported but exist in the database
        #   get added to the document's unsupported_attributes field.
        #Get database names for all fields that *should* exist on the object.
        db_fields = [val.db_field for key,val in cls._fields.iteritems()]
        #custom __setattr__ does logic of moving fields to unsupported_fields
        [doc.__setattr__("%s"%key, val) for key,val in son.iteritems()
            if key not in db_fields]

        #After a document is retrieved from the database, and any unsupported
        #   fields have been moved to unsupported_attrs, make sure the original
        #   fields will get removed from the document when it's saved.
        if hasattr(doc, 'unsupported_attrs'):
            if doc.unsupported_attrs is not None:
                for attr in doc.unsupported_attrs:
                    #mark for deletion
                    if not hasattr(doc, '_changed_fields'):
                        doc._changed_fields = []
                    doc._changed_fields.append(attr)

        # Check for a schema_version. Raise exception so we don't
        # infinitely loop through attempting to migrate.
        if hasattr(doc, 'schema_version'):
            if doc.schema_version == 0:
                raise UnrecognizedSchemaError(doc)

        # perform migration, if needed
        if hasattr(doc, '_meta'):
            if ('schema_version' in doc and
                'latest_schema_version' in doc._meta and
                doc.schema_version < doc._meta['latest_schema_version']):
                # mark for migration
                doc._meta['needs_migration'] = True
                # reload doc to get full document from database
            if (doc._meta.get('needs_migration', False) and
                not doc._meta.get('migrating', False)):
                doc._meta['migrating'] = True
                doc.reload()
                try:
                    doc.migrate()
                    doc._meta['migrated'] = True
                    doc._meta['needs_migration'] = False
                    doc._meta['migrating'] = False
                except Exception as e:
                    e.tlo = doc.id
                    raise e

        return doc

    def migrate(self):
        """
        Should be overridden by classes which inherit this class.
        """

        pass

    def merge(self, arg_dict=None, overwrite=False, **kwargs):
        """
        Merge a dictionary into a top-level object class.

        :param arg_dict: The dictionary to get data from.
        :type arg_dict: dict
        :param overwrite: Whether or not to overwrite data in the object.
        :type overwrite: boolean
        """

        merge(self, arg_dict=arg_dict, overwrite=overwrite)

    def to_csv(self, fields=[],headers=False):
        """
        Convert a class into a CSV.

        :param fields: Fields to include in the CSV.
        :type fields: list
        :param headers: Whether or not to write out column headers.
        :type headers: boolean
        :returns: str
        """

        if not fields:
            fields = self._data.keys()
        csv_string = io.BytesIO()
        csv_wr = csv.writer(csv_string)
        if headers:
            csv_wr.writerow([f.encode('utf-8') for f in fields])
        # Build the CSV Row
        row = []
        for field in fields:
            if field in self._data:
                data = ""
                if field == "aliases" and self._has_method("get_aliases"):
                    data = ";".join(self.get_aliases())
                elif field == "campaign" and self._has_method("get_campaign_names"):
                    data = ';'.join(self.get_campaign_names())
                elif field == "source" and self._has_method("get_source_names"):
                    data = ';'.join(self.get_source_names())
                elif field == "tickets":
                    data = ';'.join(self.get_tickets())
                else:
                    data = self._data[field]
                    if not hasattr(data, 'encode'):
                        # Convert non-string data types
                        data = unicode(data)
                row.append(data.encode('utf-8'))

        csv_wr.writerow(row)
        return csv_string.getvalue()


    def to_dict(self, exclude=[], include=[]):
        """
        Return the object's _data as a python dictionary.

        All fields will be converted to base python types so that
        no MongoEngine fields remain.

        :param exclude: list of fields to exclude in the result.
        :type exclude: list
        :param include: list of fields to include in the result.
        :type include: list
        :returns: dict
        """

        #MongoEngine's to_mongo() returns an object in a MongoDB friendly
        #   dictionary format. If we have no extra processing to do, just
        #   return that.
        data = self.to_mongo()
        #
        # Include, Exclude, return

        # Check projection in db_field_map
        # After the to_mongo, the fields have changed
        newproj = []
        for p in include:
            if p in self._db_field_map:
                p = self._db_field_map[p]
            elif p == "id":  # _id is not in the db_field_map
                p = "_id"
            newproj.append(p)

        if include:
            result = {}
            for k, v in data.items():
                if k in newproj and k not in exclude:
                    if k == "_id":
                        k = "id"
                    result[k] = v
            return result
        elif exclude:
            result = {}
            for k, v in data.items():
                if k in exclude:
                    continue
                if k == "_id":
                    k = "id"
                result[k] = v
            return result
        return data

    def _json_yaml_convert(self, exclude=[]):
        """
        Helper to convert to a dict before converting to JSON.

        :param exclude: list of fields to exclude.
        :type exclude: list
        :returns: json
        """

        d = self.to_dict(exclude)
        return json.dumps(d, default=json_handler)

    @classmethod
    def from_json(cls, json_data):
        """
        Converts JSON data to an unsaved document instance.

        NOTE: this method already exists in mongoengine 0.8, so it can
        be removed from here when the codebase is updated.

        :returns: class which inherits from
                  :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        """

        return cls._from_son(json_util.loads(json_data))

    def to_json(self, exclude=[]):
        """
        Convert to JSON.

        :param exclude: list of fields to exclude.
        :type exclude: list
        :returns: json
        """

        return self._json_yaml_convert(exclude)

    @classmethod
    def from_yaml(cls, yaml_data):
        """
        Converts YAML data to an unsaved document instance.

        :returns: class which inherits from
                  :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        """

        return cls._from_son(yaml.load(yaml_data))

    def to_yaml(self, exclude=[]):
        """
        Convert to JSON.

        :param exclude: list of fields to exclude.
        :type exclude: list
        :returns: json
        """

        return yaml.dump(yaml.load(self._json_yaml_convert(exclude)),
            default_flow_style=False)

    def __str__(self):
        """
        Allow us to print the class in a readable fashion.

        :returns: str
        """

        return pformat(self.to_dict())


class EmbeddedPreferredAction(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Preferred Action
    """

    object_type = StringField()
    object_field = StringField()
    object_value = StringField()


class Action(CritsDocument, CritsSchemaDocument, Document):
    """
    Action type class.
    """

    meta = {
        "collection": settings.COL_IDB_ACTIONS,
        "crits_type": 'Action',
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'The name of this Action',
            'active': 'Enabled in the UI (on/off)',
            'object_types': 'List of TLOs this is for',
            'preferred': 'List of dictionaries defining where this is preferred'
        },
    }

    name = StringField()
    active = StringField(default="on")
    object_types = ListField(StringField())
    preferred = ListField(EmbeddedDocumentField(EmbeddedPreferredAction))

class EmbeddedAction(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded action class.
    """

    action_type = StringField()
    active = StringField()
    analyst = StringField()
    begin_date = CritsDateTimeField(default=datetime.datetime.now)
    date = CritsDateTimeField(default=datetime.datetime.now)
    end_date = CritsDateTimeField()
    performed_date = CritsDateTimeField(default=datetime.datetime.now)
    reason = StringField()

class CritsActionsDocument(BaseDocument):
    """
    Inherit if you want to track actions information on a top-level object.
    """

    actions = ListField(EmbeddedDocumentField(EmbeddedAction))

    def add_action(self, type_, active, analyst, begin_date,
                   end_date, performed_date, reason, date=None):
        """
        Add an action to an Indicator.

        :param type_: The type of action.
        :type type_: str
        :param active: Whether this action is active or not.
        :param active: str ("on", "off")
        :param analyst: The user adding this action.
        :type analyst: str
        :param begin_date: The date this action begins.
        :type begin_date: datetime.datetime
        :param end_date: The date this action ends.
        :type end_date: datetime.datetime
        :param performed_date: The date this action was performed.
        :type performed_date: datetime.datetime
        :param reason: The reason for this action.
        :type reason: str
        :param date: The date this action was added to CRITs.
        :type date: datetime.datetime
        """

        ea = EmbeddedAction()
        ea.action_type = type_
        ea.active = active
        ea.analyst = analyst
        ea.begin_date = begin_date
        ea.end_date = end_date
        ea.performed_date = performed_date
        ea.reason = reason
        if date:
            ea.date = date
        self.actions.append(ea)

    def delete_action(self, date=None, action=None):
        """
        Delete an action.

        :param date: The date of the action to delete.
        :type date: datetime.datetime
        :param action: The action to delete.
        :type action: str
        """

        if not date or not action:
            return
        for t in self.actions:
            if t.date == date and t.action_type == action:
                self.actions.remove(t)
                break

    def edit_action(self, type_, active, analyst, begin_date,
                    end_date, performed_date, reason, date=None):
        """
        Edit an action for an Indicator.

        :param type_: The type of action.
        :type type_: str
        :param active: Whether this action is active or not.
        :param active: str ("on", "off")
        :param analyst: The user editing this action.
        :type analyst: str
        :param begin_date: The date this action begins.
        :type begin_date: datetime.datetime
        :param end_date: The date this action ends.
        :type end_date: datetime.datetime
        :param performed_date: The date this action was performed.
        :type performed_date: datetime.datetime
        :param reason: The reason for this action.
        :type reason: str
        :param date: The date this action was added to CRITs.
        :type date: datetime.datetime
        """

        if not date:
            return
        for t in self.actions:
            if t.date == date and t.action_type == type_:
                self.actions.remove(t)
                ea = EmbeddedAction()
                ea.action_type = type_
                ea.active = active
                ea.analyst = analyst
                ea.begin_date = begin_date
                ea.end_date = end_date
                ea.performed_date = performed_date
                ea.reason = reason
                ea.date = date
                self.actions.append(ea)
                break

# Embedded Documents common to most classes
class EmbeddedSource(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Source.
    """

    class SourceInstance(EmbeddedDocument, CritsDocumentFormatter):
        """
        Information on the instance of this source.
        """

        analyst = StringField()
        date = CritsDateTimeField(default=datetime.datetime.now)
        method = StringField()
        reference = StringField()
        tlp = StringField(default='red', choices=('white', 'green', 'amber', 'red'))

        def __eq__(self, other):
            """
            Two source instances are equal if their data attributes are equal
            """

            if isinstance(other, type(self)):
                if (self.analyst == other.analyst and
                    self.date == other.date and
                    self.method == other.method and
                    self.reference == other.reference):
                    # all data attributes are equal, so sourceinstances are equal
                    return True
            return False

    instances = ListField(EmbeddedDocumentField(SourceInstance))
    name = StringField()

class CritsSourceDocument(BaseDocument):
    """
    Inherit if you want to track source information on a top-level object.
    """

    source = ListField(EmbeddedDocumentField(EmbeddedSource), required=True)

    def add_source(self, source_item=None, source=None, method='',
                   reference='', date=None, analyst=None, tlp=None):
        """
        Add a source instance to this top-level object.

        :param source_item: An entire source instance.
        :type source_item: :class:`crits.core.crits_mongoengine.EmbeddedSource`
        :param source: Name of the source.
        :type source: str
        :param method: Method of acquisition.
        :type method: str
        :param reference: Reference to the data from the source.
        :type reference: str
        :param date: The date of acquisition.
        :type date: datetime.datetime
        :param analyst: The user adding the source instance.
        :type analyst: str
        :param tlp: The TLP level this data was shared under.
        :type tlp: str
        """

        sc = len(self.source)
        s = None
        if source and analyst and tlp:
            if tlp not in ('white', 'green', 'amber', 'red'):
                tlp = 'red'
            if not date:
                date = datetime.datetime.now()
            s = EmbeddedSource()
            s.name = source
            i = EmbeddedSource.SourceInstance()
            i.date = date
            i.reference = reference
            i.method = method
            i.analyst = analyst
            i.tlp = tlp
            s.instances = [i]
        if not isinstance(source_item, EmbeddedSource):
            source_item = s

        if isinstance(source_item, EmbeddedSource):
            match = None
            if method or reference or tlp: # use method, reference, and tlp
                for instance in source_item.instances:
                    instance.method = method or instance.method
                    instance.reference = reference or instance.reference
                    instance.tlp = tlp or instance.tlp
            for c, s in enumerate(self.source):
                if s.name == source_item.name: # find index of matching source
                    match = c
                    break
            if match is not None: # if source exists, add instances to it
                # Don't add exact duplicates
                for new_inst in source_item.instances:
                    for exist_inst in self.source[match].instances:
                        if new_inst == exist_inst:
                            break
                    else:
                        self.source[match].instances.append(new_inst)
            else: # else, add as new source
                self.source.append(source_item)
            if not sc:
                self.tlp = source_item.instances[0].tlp

    def edit_source(self, source=None, date=None, method='',
                    reference='', analyst=None, tlp=None):
        """
        Edit a source instance from this top-level object.

        :param source: Name of the source.
        :type source: str
        :param date: The date of acquisition to match on.
        :type date: datetime.datetime
        :param method: Method of acquisition.
        :type method: str
        :param reference: Reference to the data from the source.
        :type reference: str
        :param analyst: The user editing the source instance.
        :type analyst: str
        :param tlp: The TLP this data was shared under.
        :type tlp: str
        """

        if tlp not in ('white', 'green', 'amber', 'red'):
            tlp = 'red'
        if source and date:
            for c, s in enumerate(self.source):
                if s.name == source:
                    for i, si in enumerate(s.instances):
                        if si.date == date:
                            self.source[c].instances[i].method = method
                            self.source[c].instances[i].reference = reference
                            self.source[c].instances[i].analyst = analyst
                            self.source[c].instances[i].tlp = tlp

    def remove_source(self, source=None, date=None, remove_all=False):
        """
        Remove a source or source instance from a top-level object.

        :param source: Name of the source.
        :type source: str
        :param date: Date to match on.
        :type date: datetime.datetime
        :param remove_all: Remove all instances of this source.
        :type remove_all: boolean
        :returns: dict with keys "success" (boolean) and "message" (str)
        """

        keepone = {'success': False,
                   'message': "Must leave at least one source for access controls.  "
                   "If you wish to change the source, please assign a new source and then remove the old."}

        if not source:
            return {'success': False,
                    'message': 'No source to locate'}
        if not remove_all and not date:
            return {'success': False,
                    'message': 'Not removing all and no date to find.'}
        for s in self.source:
            if s.name == source:
                if remove_all:
                    if len(self.source) > 1:
                        self.source.remove(s)
                        message = "Deleted source %s" % source
                        return {'success': True,
                                'message': message}
                    else:
                        return keepone
                else:
                    for si in s.instances:
                        if si.date == date:
                            if len(s.instances) > 1:
                                s.instances.remove(si)
                                message = "Deleted instance of  %s" % source
                                return {'success': True,
                                        'message': message}
                            else:
                                if len(self.source) > 1:
                                    self.source.remove(s)
                                    message = "Deleted source %s" % source
                                    return {'success': True,
                                            'message': message}
                                else:
                                    return keepone

    def sanitize_sources(self, username=None, sources=None):
        """
        Sanitize the source list down to only those a user has access to see.

        :param username: The user requesting this data.
        :type username: str
        :param sources: A list of sources the user has access to.
        :type sources: list
        """

        if username and hasattr(self, 'source'):
            length = len(self.source)
            if not sources:
                sources = user_sources(username)
            # use slice to modify in place in case any code is referencing
            # the source already will reflect the changes as well
            self.source[:] = [s for s in self.source if s.name in sources]
            # a bit of a hack but we add a poorly formatted source to the
            # source list which has an instances length equal to the amount
            # of sources that were sanitized out of the user's list.
            # not tested but this has the added benefit of throwing a
            # ValidationError if someone were to try and save() this.
            new_length = len(self.source)
            if length > new_length:
                i_length = length - new_length
                s = EmbeddedSource()
                s.name = "Other"
                s.instances = [0] * i_length
                self.source.append(s)

    def get_source_names(self):
        """
        Return a list of source names that have provided this data.
        """

        return [obj['name'] for obj in self._data['source']]


class EmbeddedTicket(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Ticket Class.
    """

    analyst = StringField()
    date = CritsDateTimeField(default=datetime.datetime.now)
    ticket_number = StringField()

class EmbeddedTickets(BaseDocument):
    """
    Embedded Tickets List.
    """

    tickets = ListField(EmbeddedDocumentField(EmbeddedTicket))

    def is_ticket_exist(self, ticket_number):
        """
        Does this ticket already exist?

        :param ticket_number: The ticket to look for.
        :type ticket_number: str
        :returns: True, False
        """

        for ticket in self.tickets:
            if ticket_number == ticket.ticket_number:
                return True;

        return False;

    def add_ticket(self, tickets, analyst=None, date=None):
        """
        Add a ticket to this top-level object.

        :param tickets: The ticket(s) to add.
        :type tickets: str, list, or
                       :class:`crits.core.crits_mongoengine.EmbeddedTicket`
        :param analyst: The user adding this ticket.
        :type analyst: str
        :param date: The date for the ticket.
        :type date: datetime.datetime.
        """

        if isinstance(tickets, basestring):
            tickets = tickets.split(',')
        elif not isinstance(tickets, list):
            tickets = [tickets]

        for ticket in tickets:
            if isinstance(ticket, EmbeddedTicket):
                if not self.is_ticket_exist(ticket.ticket_number): # stop dups
                    self.tickets.append(ticket)
            elif isinstance(ticket, basestring):
                if ticket and not self.is_ticket_exist(ticket):  # stop dups
                    et = EmbeddedTicket()
                    et.analyst = analyst
                    et.ticket_number = ticket
                    if date:
                        et.date = date
                    self.tickets.append(et)

    def edit_ticket(self, analyst, ticket_number, date=None):
        """
        Edit a ticket this top-level object.

        :param analyst: The user editing this ticket.
        :type analyst: str
        :param ticket_number: The new ticket value.
        :type ticket_number: str
        :param date: The date for the ticket.
        :type date: datetime.datetime.
        """

        if not date:
            return
        for t in self.tickets:
            if t.date == date:
                self.tickets.remove(t)
                et = EmbeddedTicket()
                et.analyst = analyst
                et.ticket_number = ticket_number
                et.date = date
                self.tickets.append(et)
                break

    def delete_ticket(self, date=None):
        """
        Delete a ticket from this top-level object.

        :param date: The date the ticket was added.
        :type date: datetime.datetime
        """

        if not date:
            return
        for t in self.tickets:
            if t.date == date:
                self.tickets.remove(t)
                break

    def get_tickets(self):
        """
        Get the tickets for this top-level object.

        :returns: list
        """

        return [obj['ticket_number'] for obj in self._data['tickets']]


class EmbeddedCampaign(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Campaign Class.
    """

    analyst = StringField()
    confidence = StringField(default='low', choices=('low', 'medium', 'high'))
    date = CritsDateTimeField(default=datetime.datetime.now)
    description = StringField()
    name = StringField(required=True)


class EmbeddedLocation(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Location object
    """

    location_type = StringField(required=True)
    location = StringField(required=True)
    description = StringField(required=False)
    latitude = StringField(required=False)
    longitude = StringField(required=False)
    analyst = StringField(required=True)
    date = DateTimeField(default=datetime.datetime.now)


class Releasability(EmbeddedDocument, CritsDocumentFormatter):
    """
    Releasability Class.
    """

    class ReleaseInstance(EmbeddedDocument, CritsDocumentFormatter):
        """
        Releasability Instance Class.
        """

        analyst = StringField()
        date = DateTimeField()
        note = StringField()


    name = StringField()
    analyst = StringField()
    instances = ListField(EmbeddedDocumentField(ReleaseInstance))


class UnrecognizedSchemaError(ValidationError):
    """
    Error if the schema for a document is not found or unrecognized.
    """

    def __init__(self, doc, **kwargs):
        message = "Document schema is unrecognized: %s" % doc.schema_version
        self.schema = doc._meta['schema_doc']
        self.doc = doc.to_dict()
        super(UnrecognizedSchemaError, self).__init__(message=message,
            field_name='schema_version', **kwargs)


class EmbeddedObject(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Object Class.
    """

    analyst = StringField()
    date = CritsDateTimeField(default=datetime.datetime.now)
    source = ListField(EmbeddedDocumentField(EmbeddedSource), required=True)
    object_type = StringField(required=True, db_field="type")
    value = StringField(required=True)


class EmbeddedRelationship(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Relationship Class.
    """

    relationship = StringField(required=True)
    relationship_date = CritsDateTimeField()
    object_id = ObjectIdField(required=True, db_field="value")
    date = CritsDateTimeField(default=datetime.datetime.now)
    rel_type = StringField(db_field="type", required=True)
    analyst = StringField()
    rel_reason = StringField()
    rel_confidence = StringField(default='unknown', required=True)

class CritsBaseAttributes(CritsDocument, CritsBaseDocument,
                          CritsSchemaDocument, CritsStatusDocument, EmbeddedTickets):
    """
    CRITs Base Attributes Class. The main class that should be inherited if you
    are making a new top-level object. Adds all of the standard top-level object
    features.
    """

    analyst = StringField()
    bucket_list = ListField(StringField())
    campaign = ListField(EmbeddedDocumentField(EmbeddedCampaign))
    locations = ListField(EmbeddedDocumentField(EmbeddedLocation))
    description = StringField()
    obj = ListField(EmbeddedDocumentField(EmbeddedObject), db_field="objects")
    relationships = ListField(EmbeddedDocumentField(EmbeddedRelationship))
    releasability = ListField(EmbeddedDocumentField(Releasability))
    screenshots = ListField(StringField())
    sectors = ListField(StringField())
    tlp = StringField(default='red', choices=('white', 'green', 'amber', 'red'))

    def set_tlp(self, tlp):
        """
        Set the TLP of this TLO.

        :param tlp: The TLP to set.
        """

        if tlp not in ('white', 'green', 'amber', 'red'):
            tlp = 'red'
        if tlp in self.get_acceptable_tlp_levels():
            self.tlp = tlp

    def get_acceptable_tlp_levels(self):
        """
        Based on what TLP levels sources have shared, limit the list of TLP
        levels you can share this with accordingly.

        :returns: list
        """

        d = {'white': ['white', 'green', 'amber', 'red'],
             'green': ['green', 'amber', 'red'],
             'amber': ['amber', 'red'],
             'red': ['red']}

        my_tlps = []
        for s in self.source:
            for i in s.instances:
                my_tlps.append(i.tlp)
        my_tlps = OrderedDict.fromkeys(my_tlps).keys()

        if 'white' in my_tlps:
            return d['white']
        elif 'green' in my_tlps:
            return d['green']
        elif 'amber' in my_tlps:
            return d['amber']
        else:
            return d['red']

    def add_campaign(self, campaign_item=None, update=True):
        """
        Add a campaign to this top-level object.

        :param campaign_item: The campaign to add.
        :type campaign_item: :class:`crits.core.crits_mongoengine.EmbeddedCampaign`
        :param update: If True, allow merge with pre-existing campaigns
        :              If False, do not change any pre-existing campaigns
        :type update:  boolean
        :returns: dict with keys "success" (boolean) and "message" (str)
        """

        if isinstance(campaign_item, EmbeddedCampaign):
            if campaign_item.name != None and campaign_item.name.strip() != '':
                campaign_item.confidence = campaign_item.confidence.strip().lower()
                if campaign_item.confidence == '':
                    campaign_item.confidence = 'low'
                for c, campaign in enumerate(self.campaign):
                    if campaign.name == campaign_item.name:
                        if not update:
                            return {'success': False, 'message': 'This Campaign is already assigned.'}
                        con = {'low': 1, 'medium': 2, 'high': 3}
                        if con.get(campaign.confidence, 0) < con.get(campaign_item.confidence):
                            self.campaign[c].confidence = campaign_item.confidence
                            self.campaign[c].analyst = campaign_item.analyst
                        break
                else:
                    self.campaign.append(campaign_item)
                return {'success': True, 'message': 'Campaign assigned successfully!'}
        return {'success': False, 'message': 'Campaign is invalid'}

    def remove_campaign(self, campaign_name=None, campaign_date=None):
        """
        Remove a campaign from this top-level object.

        :param campaign_name: The campaign to remove.
        :type campaign_name: str
        :param campaign_date: The date the campaign was added.
        :type campaign_date: datetime.datetime.
        """

        for campaign in self.campaign:
            if campaign.name == campaign_name or campaign.date == campaign_date:
                self.campaign.remove(campaign)
                break

    def edit_campaign(self, campaign_name=None, campaign_item=None):
        """
        Edit an existing Campaign. This just removes the old entry and adds a
        new one.

        :param campaign_name: The campaign to remove.
        :type campaign_name: str
        :param campaign_item: The campaign to add.
        :type campaign_item: :class:`crits.core.crits_mongoengine.EmbeddedCampaign`
        """

        if isinstance(campaign_item, EmbeddedCampaign):
            self.remove_campaign(campaign_name=campaign_item.name)
            self.add_campaign(campaign_item=campaign_item)

    def add_location(self, location_item=None):
        """
        Add a location to this top-level object.

        :param location_item: The location to add.
        :type location_item: :class:`crits.core.crits_mongoengine.EmbeddedLocation`
        :returns: dict with keys "success" (boolean) and "message" (str)
        """

        if isinstance(location_item, EmbeddedLocation):
            if (location_item.location != None and
                location_item.location.strip() != ''):
                for l, location in enumerate(self.locations):
                    if (location.location == location_item.location and
                        location.location_type == location_item.location_type and
                        location.date == location_item.date):
                        return {'success': False,
                                'message': 'This location is already assigned.'}
                else:
                    self.locations.append(location_item)
                return {'success': True,
                        'message': 'Location assigned successfully!'}
        return {'success': False,
                'message': 'Location is invalid'}

    def edit_location(self, location_name=None, location_type=None, date=None,
                      description=None, latitude=None, longitude=None):
        """
        Edit a location.

        :param location_name: The location_name to edit.
        :type location_name: str
        :param location_type: The location_type to edit.
        :type location_type: str
        :param date: The location date to edit.
        :type date: str
        :param description: The new description.
        :type description: str
        :param latitude: The new latitude.
        :type latitude: str
        :param longitude: The new longitude.
        :type longitude: str
        """

        if isinstance(date, basestring):
            date = parse(date, fuzzy=True)
        for location in self.locations:
            if (location.location == location_name and
                location.location_type == location_type and
                location.date == date):
                if description:
                    location.description = description
                if latitude:
                    location.latitude = latitude
                if longitude:
                    location.longitude = longitude
                break

    def remove_location(self, location_name=None, location_type=None, date=None):
        """
        Remove a location from this top-level object.

        :param location_name: The location to remove.
        :type location_name: str
        :param location_type: The location type.
        :type location_type: str
        :param date: The location date.
        :type date: str
        """

        if isinstance(date, basestring):
            date = parse(date, fuzzy=True)
        for location in self.locations:
            if (location.location == location_name and
                location.location_type == location_type and
                location.date == date):
                self.locations.remove(location)
                break

    def add_bucket_list(self, tags, analyst, append=True):
        """
        Add buckets to this top-level object.

        :param tags: The buckets to be added.
        :type tags: list, str
        :param analyst: The analyst adding these buckets.
        :type analyst: str
        :param append: Whether or not to replace or append these buckets.
        :type append: boolean
        """

        from crits.core.handlers import alter_bucket_list
        # Track the addition or subtraction of tags.
        # Get the bucket_list for the object, find out if this is an addition
        # or subtraction of a bucket_list.
        if isinstance(tags, list) and len(tags) == 1 and tags[0] == '':
            parsed_tags = []
        elif isinstance(tags, (str, unicode)):
            parsed_tags = tags.split(',')
        else:
            parsed_tags = tags

        parsed_tags = [t.strip() for t in parsed_tags]

        names = None
        if len(self.bucket_list) >= len(parsed_tags):
            names = [x for x in self.bucket_list if x not in parsed_tags and x != '']
            val = -1
        else:
            names = [x for x in parsed_tags if x not in self.bucket_list and x != '']
            val = 1

        if names:
            alter_bucket_list(self, names, val)

        if append:
            for t in parsed_tags:
                if t and t not in self.bucket_list:
                    self.bucket_list.append(t)
        else:
            self.bucket_list = parsed_tags

    def get_bucket_list_string(self):
        """
        Collapse the list of buckets into a single comma-separated string.

        :returns: str
        """

        return ','.join(str(x) for x in self.bucket_list)

    def add_sector_list(self, sectors, analyst, append=True):
        """
        Add sectors to this top-level object.

        :param sectors: The sectors to be added.
        :type tags: list, str
        :param analyst: The analyst adding these sectors.
        :type analyst: str
        :param append: Whether or not to replace or append these sectors.
        :type append: boolean
        """

        from crits.core.handlers import alter_sector_list
        # Track the addition or subtraction of tags.
        # Get the sectors for the object, find out if this is an addition
        # or subtraction of a sector.
        if isinstance(sectors, list) and len(sectors) == 1 and sectors[0] == '':
            parsed_sectors = []
        elif isinstance(sectors, (str, unicode)):
            parsed_sectors = sectors.split(',')
        else:
            parsed_sectors = sectors

        parsed_sectors = [s.strip() for s in parsed_sectors]

        names = None
        if len(self.sectors) >= len(parsed_sectors):
            names = [x for x in self.sectors if x not in parsed_sectors and x != '']
            val = -1
        else:
            names = [x for x in parsed_sectors if x not in self.sectors and x != '']
            val = 1

        if names:
            alter_sector_list(self, names, val)

        if append:
            for t in parsed_sectors:
                if t not in self.sectors:
                    self.sectors.append(t)
        else:
            self.sectors = parsed_sectors

    def get_sectors_list_string(self):
        """
        Collapse the list of sectors into a single comma-separated string.

        :returns: str
        """

        return ','.join(str(x) for x in self.sectors)

    def get_comments(self):
        """
        Get the comments for this top-level object.

        :returns: list
        """

        from crits.comments.handlers import get_comments
        comments = get_comments(self.id, self._meta['crits_type'])
        return comments

    def delete_all_comments(self):
        """
        Delete all comments for this top-level object.
        """

        from crits.comments.comment import Comment
        Comment.objects(obj_id=self.id,
                        obj_type=self._meta['crits_type']).delete()

    def get_screenshots(self, analyst):
        """
        Get the screenshots for this top-level object.

        :returns: list
        """

        from crits.screenshots.handlers import get_screenshots_for_id
        screenshots = get_screenshots_for_id(self._meta['crits_type'],
                                             self.id,
                                             analyst,
                                             True)
        if 'screenshots' in screenshots:
            return screenshots['screenshots']
        else:
            return []

    def add_object(self, object_type, value, source, method, reference,
                   analyst, object_item=None):
        """
        Add an object to this top-level object.

        :param object_type: The Object Type being added.
        :type object_type: str
        :param value: The value of the object being added.
        :type value: str
        :param source: The name of the source adding this object.
        :type source: str
        :param method: The method in which the object was added or gathered.
        :type method: str
        :param reference: A reference to the original object.
        :type reference: str
        :param analyst: The user adding this object.
        :type analyst: str
        :param object_item: An entire object ready to be added.
        :type object_item: :class:`crits.core.crits_mongoengine.EmbeddedObject`
        :returns: dict with keys:
                  "success" (boolean)
                  "message" (str)
                  "object"  (EmbeddedObject)
        """

        if not isinstance(object_item, EmbeddedObject):
            object_item = EmbeddedObject()
            object_item.analyst = analyst
            src = create_embedded_source(source,
                                                         method=method,
                                                         reference=reference,
                                                         needs_tlp=False,
                                                         analyst=analyst)

            if not src:
                return {'success': False, 'message': 'Invalid Source'}
            object_item.source = [src]
            object_item.object_type = object_type
            object_item.value = value
        for o in self.obj:
            if (o.object_type == object_item.object_type
                and o.value == object_item.value):
                return {'success': False, 'object': o,
                        'message': 'Object already exists'}

        self.obj.append(object_item)
        return {'success': True, 'object': object_item}

    def remove_object(self, object_type, value):
        """
        Remove an object from this top-level object.

        :param object_type: The type of the object being removed.
        :type object_type: str
        :param value: The value of the object being removed.
        :type value: str
        """

        for o in self.obj:
            if (o.object_type == object_type and
                o.value == value):
                from crits.objects.handlers import delete_object_file
                self.obj.remove(o)
                delete_object_file(value)
                break

    def delete_all_analysis_results(self):
        """
        Delete all analysis results for this top-level object.
        """

        from crits.services.analysis_result import AnalysisResult
        results = AnalysisResult.objects(object_id=str(self.id))
        for result in results:
            result.delete()

    def delete_all_objects(self):
        """
        Delete all objects for this top-level object.
        """

        from crits.objects.handlers import delete_object_file
        for o in self.obj:
            if o.object_type == ObjectTypes.FILE_UPLOAD:
                delete_object_file(o.value)
        self.obj = []

    def delete_all_favorites(self):
        """
        Delete all favorites for this top-level object.
        """

        from crits.core.user import CRITsUser
        users = CRITsUser.objects()
        for user in users:
            type_ = self._meta['crits_type']
            if type_ in user.favorites and str(self.id) in user.favorites[type_]:
                user.favorites[type_].remove(str(self.id))
                user.save()

    def update_object_value(self, object_type, value, new_value):
        """
        Update the value for an object on this top-level object.

        :param object_type: The type of the object being updated.
        :type object_type: str
        :param value: The value of the object being updated.
        :type value: str
        :param new_value: The new value of the object being updated.
        :type new_value: str
        """

        for c, o in enumerate(self.obj):
            if (o.object_type == object_type and
                o.value == value):
                self.obj[c].value = new_value
                break

    def update_object_source(self, object_type, value,
                             new_source=None, new_method='',
                             new_reference='', analyst=None):
        """
        Update the source for an object on this top-level object.

        :param object_type: The type of the object being updated.
        :type object_type: str
        :param value: The value of the object being updated.
        :type value: str
        :param new_source: The name of the new source.
        :type new_source: str
        :param new_method: The method of the new source.
        :type new_method: str
        :param new_reference: The reference of the new source.
        :type new_reference: str
        :param analyst: The user updating the source.
        :type analyst: str
        """

        for c, o in enumerate(self.obj):
            if (o.object_type == object_type and
                o.value == value):
                if not analyst:
                    analyst = self.obj[c].source[0].intances[0].analyst
                source = [create_embedded_source(new_source,
                                                 method=new_method,
                                                 reference=new_reference,
                                                 needs_tlp=False,
                                                 analyst=analyst)]
                self.obj[c].source = source
                break

    def format_campaign(self, campaign, analyst):
        """
        Render a campaign to HTML to prepare for inclusion in a template.

        :param campaign: The campaign to templetize.
        :type campaign: :class:`crits.core.crits_mongoengine.EmbeddedCampaign`
        :param analyst: The user requesting the Campaign.
        :type analyst: str
        :returns: str
        """

        html = render_to_string('campaigns_display_row_widget.html',
                                {'campaign': campaign,
                                 'hit': self,
                                 'obj': None,
                                 'relationship': {'type': self._meta['crits_type']}})
        return html

    def format_location(self, location, analyst):
        """
        Render a location to HTML to prepare for inclusion in a template.

        :param location: The location to templetize.
        :type location: :class:`crits.core.crits_mongoengine.EmbeddedLocation`
        :param analyst: The user requesting the Campaign.
        :type analyst: str
        :returns: str
        """

        html = render_to_string('locations_display_row_widget.html',
                                {'location': location,
                                 'hit': self,
                                 'obj': None,
                                 'relationship': {'type': self._meta['crits_type']}})
        return html

    def sort_objects(self):
        """
        Sort the objects for this top-level object.

        :returns: dict
        """

        o_dict = dict((o.object_type,[]) for o in self.obj)
        o_dict['Other'] = 0
        o_dict['Count'] = len(self.obj)
        for o in self.obj:
            o_dict[o.object_type].append(o.to_dict())
        return o_dict

    def add_relationship(self, rel_item, rel_type, rel_date=None,
                         analyst=None, rel_confidence='unknown',
                         rel_reason='', get_rels=False):
        """
        Add a relationship to this top-level object. The rel_item will be
        saved. It is up to the caller to save "self".

        :param rel_item: The top-level object to relate to.
        :type rel_item: class which inherits from
                        :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        :param rel_type: The type of relationship.
        :type rel_type: str
        :param rel_date: The date this relationship applies.
        :type rel_date: datetime.datetime
        :param analyst: The user forging this relationship.
        :type analyst: str
        :param rel_confidence: The confidence of the relationship.
        :type rel_confidence: str
        :param rel_reason: The reason for the relationship.
        :type rel_reason: str
        :param get_rels: If True, return all relationships after forging.
                         If False, return the new EmbeddedRelationship object
        :type get_rels: boolean
        :returns: dict with keys:
                  "success" (boolean)
                  "message" (str if failed, else dict or EmbeddedRelationship)
        """

        # Prevent class from having a relationship to itself
        if self == rel_item:
            return {'success': False,
                    'message': 'Cannot forge relationship to oneself'}

        # get reverse relationship
        rev_type = RelationshipTypes.inverse(rel_type)
        if rev_type is None:
            return {'success': False,
                    'message': 'Could not find relationship type'}

        date = datetime.datetime.now()

        # setup the relationship for me
        my_rel = EmbeddedRelationship()
        my_rel.relationship = rel_type
        my_rel.rel_type = rel_item._meta['crits_type']
        my_rel.analyst = analyst
        my_rel.date = date
        my_rel.relationship_date = rel_date
        my_rel.object_id = rel_item.id
        my_rel.rel_confidence = rel_confidence
        my_rel.rel_reason = rel_reason

        # setup the relationship for them
        their_rel = EmbeddedRelationship()
        their_rel.relationship = rev_type
        their_rel.rel_type = self._meta['crits_type']
        their_rel.analyst = analyst
        their_rel.date = date
        their_rel.relationship_date = rel_date
        their_rel.object_id = self.id
        their_rel.rel_confidence = rel_confidence
        their_rel.rel_reason = rel_reason

        # variables for detecting if an existing relationship exists
        my_existing_rel = None
        their_existing_rel = None

        # check for existing relationship before blindly adding
        for r in self.relationships:
            if (r.object_id == my_rel.object_id
                and r.relationship == my_rel.relationship
                and (not rel_date or r.relationship_date == rel_date)
                and r.rel_type == my_rel.rel_type):
                my_existing_rel = r
                break # If relationship already exists then exit loop
        for r in rel_item.relationships:
            if (r.object_id == their_rel.object_id
                and r.relationship == their_rel.relationship
                and (not rel_date or r.relationship_date == rel_date)
                and r.rel_type == their_rel.rel_type):
                their_existing_rel = r
                break # If relationship already exists then exit loop

        # If the relationship already exists on both sides then do nothing
        if my_existing_rel and their_existing_rel:
            return {'success': False,
                    'message': 'Relationship already exists'}

        # Repair unreciprocated relationships
        if not my_existing_rel: # If my rel does not exist then add it
            if their_existing_rel: # If their rel exists then use its data
                my_rel.analyst = their_existing_rel.analyst
                my_rel.date = their_existing_rel.date
                my_rel.relationship_date = their_existing_rel.relationship_date
                my_rel.rel_confidence = their_existing_rel.rel_confidence
                my_rel.rel_reason = their_existing_rel.rel_reason
            self.relationships.append(my_rel) # add my new relationship
        if not their_existing_rel: # If their rel does not exist then add it
            if my_existing_rel: # If my rel exists then use its data
                their_rel.analyst = my_existing_rel.analyst
                their_rel.date = my_existing_rel.date
                their_rel.relationship_date = my_existing_rel.relationship_date
                their_rel.rel_confidence = my_existing_rel.rel_confidence
                their_rel.rel_reason = my_existing_rel.rel_reason
            rel_item.relationships.append(their_rel) # add to passed rel_item

            # updating DB this way can be much faster than saving entire TLO
            rel_item.update(add_to_set__relationships=their_rel)

        if get_rels:
            results = {'success': True,
                       'message': self.sort_relationships(analyst, meta=True)}
        else:
            results = {'success': True,
                       'message': my_rel}

        # In case of relating to a versioned backdoor we also want to relate to
        # the family backdoor.
        self_type = self._meta['crits_type']
        rel_item_type = rel_item._meta['crits_type']

        # If both are not backdoors, just return
        if self_type != 'Backdoor' and rel_item_type != 'Backdoor':
            return results

        # If either object is a family backdoor, don't go further.
        if ((self_type == 'Backdoor' and self.version == '') or
            (rel_item_type == 'Backdoor' and rel_item.version == '')):
            return results

        # If one is a versioned backdoor and the other is a family backdoor,
        # don't go further.
        if ((self_type == 'Backdoor' and self.version != '' and
             rel_item_type == 'Backdoor' and rel_item.version == '') or
            (rel_item_type == 'Backdoor' and rel_item.version != '' and
             self_type == 'Backdoor' and self.version == '')):
           return results

        # Figure out which is the backdoor object.
        if self_type == 'Backdoor':
            bd = self
            other = rel_item
        else:
            bd = rel_item
            other = self

        # Find corresponding family backdoor object.
        klass = class_from_type('Backdoor')
        family = klass.objects(name=bd.name, version='').first()
        if family:
            other.add_relationship(family,
                                   rel_type,
                                   rel_date=rel_date,
                                   analyst=analyst,
                                   rel_confidence=rel_confidence,
                                   rel_reason=rel_reason,
                                   get_rels=get_rels)
            other.save(user=analyst)

        return results

    def _modify_relationship(self, rel_item=None, rel_id=None, type_=None,
                             rel_type=None, rel_date=None, new_type=None,
                             new_date=None, new_confidence='unknown',
                             new_reason="N/A", modification=None, analyst=None):
        """
        Modify a relationship to this top-level object. If rel_item is provided it
        will be used, otherwise rel_id and type_ must be provided.

        :param rel_item: The top-level object to relate to.
        :type rel_item: class which inherits from
                        :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        :param rel_id: The ObjectId of the top-level object to relate to.
        :type rel_id: str
        :param type_: The type of top-level object to relate to.
        :type type_: str
        :param rel_type: The type of relationship.
        :type rel_type: str
        :param rel_date: The date this relationship applies.
        :type rel_date: datetime.datetime
        :param new_type: The new relationship type.
        :type new_type: str
        :param new_date: The new relationship date.
        :type new_date: datetime.datetime
        :param new_confidence: The new confidence.
        :type new_confidence: str
        :param new_reason: The new reason.
        :type new_reason: str
        :param modification: What type of modification this is ("type",
                             "delete", "date", "confidence").
        :type modification: str
        :param analyst: The user forging this relationship.
        :type analyst: str
        :returns: dict with keys "success" (boolean) and "message" (str)
        """
        got_rel = True
        if not rel_item:
            got_rel = False
            if isinstance(rel_id, basestring) and isinstance(type_, basestring):
                rel_item = class_from_id(type_, rel_id)
            else:
                return {'success': False,
                        'message': 'Could not find object'}
        if isinstance(new_date, basestring):
            new_date = parse(new_date, fuzzy=True)
        if rel_item and rel_type and modification:
            # get reverse relationship
            rev_type = RelationshipTypes.inverse(rel_type)
            if rev_type is None:
                return {'success': False,
                        'message': 'Could not find relationship type'}
            if modification == "type":
                # get new reverse relationship
                new_rev_type = RelationshipTypes.inverse(new_type)
                if new_rev_type is None:
                    return {'success': False,
                            'message': 'Could not find reverse relationship type'}
            for c, r in enumerate(self.relationships):
                if rel_date:
                    if (r.object_id == rel_item.id
                        and r.relationship == rel_type
                        and r.relationship_date == rel_date
                        and r.rel_type == rel_item._meta['crits_type']):
                        if modification == "type":
                            self.relationships[c].relationship = new_type
                        elif modification == "date":
                            self.relationships[c].relationship_date = new_date
                        elif modification == "confidence":
                            self.relationships[c].rel_confidence = new_confidence
                        elif modification == "reason":
                            self.relationships[c].rel_reason = new_reason
                        elif modification == "delete":
                            del self.relationships[c]
                else:
                    if (r.object_id == rel_item.id
                        and r.relationship == rel_type
                        and r.rel_type == rel_item._meta['crits_type']):
                        if modification == "type":
                            self.relationships[c].relationship = new_type
                        elif modification == "date":
                            self.relationships[c].relationship_date = new_date
                        elif modification == "confidence":
                            self.relationships[c].rel_confidence = new_confidence
                        elif modification == "reason":
                            self.relationships[c].rel_reason = new_reason
                        elif modification == "delete":
                            del self.relationships[c]
            for c, r in enumerate(rel_item.relationships):
                if rel_date:
                    if (r.object_id == self.id
                        and r.relationship == rev_type
                        and r.relationship_date == rel_date
                        and r.rel_type == self._meta['crits_type']):
                        if modification == "type":
                            rel_item.relationships[c].relationship = new_rev_type
                        elif modification == "date":
                            rel_item.relationships[c].relationship_date = new_date
                        elif modification == "confidence":
                            rel_item.relationships[c].rel_confidence = new_confidence
                        elif modification == "reason":
                            rel_item.relationships[c].rel_reason = new_reason
                        elif modification == "delete":
                            del rel_item.relationships[c]
                else:
                    if (r.object_id == self.id
                        and r.relationship == rev_type
                        and r.rel_type == self._meta['crits_type']):
                        if modification == "type":
                            rel_item.relationships[c].relationship = new_rev_type
                        elif modification == "date":
                            rel_item.relationships[c].relationship_date = new_date
                        elif modification == "confidence":
                            rel_item.relationships[c].rel_confidence = new_confidence
                        elif modification == "reason":
                            rel_item.relationships[c].rel_reason = new_reason
                        elif modification == "delete":
                            del rel_item.relationships[c]
            if not got_rel:
                rel_item.save(username=analyst)
            if modification == "delete":
                return {'success': True,
                        'message': 'Relationship deleted'}
            else:
                return {'success': True,
                        'message': 'Relationship modified'}
        else:
            return {'success': False,
                    'message': 'Need valid object and relationship type'}

    def edit_relationship_date(self, rel_item=None, rel_id=None, type_=None, rel_type=None,
                               rel_date=None, new_date=None, analyst=None):
        """
        Modify a relationship date for a relationship to this top-level object.
        If rel_item is provided it will be used, otherwise rel_id and type_ must
        be provided.

        :param rel_item: The top-level object to relate to.
        :type rel_item: class which inherits from
                        :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        :param rel_id: The ObjectId of the top-level object to relate to.
        :type rel_id: str
        :param type_: The type of top-level object to relate to.
        :type type_: str
        :param rel_type: The type of relationship.
        :type rel_type: str
        :param rel_date: The date this relationship applies.
        :type rel_date: datetime.datetime
        :param new_date: The new relationship date.
        :type new_date: datetime.datetime
        :param analyst: The user editing this relationship.
        :type analyst: str
        :returns: dict with keys "success" (boolean) and "message" (str)
        """

        return self._modify_relationship(rel_item=rel_item, rel_id=rel_id,
                             type_=type_, rel_type=rel_type,
                             rel_date=rel_date, new_date=new_date,
                             modification="date", analyst=analyst)

    def edit_relationship_type(self, rel_item=None, rel_id=None, type_=None, rel_type=None,
                               rel_date=None, new_type=None, analyst=None):
        """
        Modify a relationship type for a relationship to this top-level object.
        If rel_item is provided it will be used, otherwise rel_id and type_ must
        be provided.

        :param rel_item: The top-level object to relate to.
        :type rel_item: class which inherits from
                        :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        :param rel_id: The ObjectId of the top-level object to relate to.
        :type rel_id: str
        :param type_: The type of top-level object to relate to.
        :type type_: str
        :param rel_type: The type of relationship.
        :type rel_type: str
        :param rel_date: The date this relationship applies.
        :type rel_date: datetime.datetime
        :param new_type: The new relationship type.
        :type new_type: str
        :param analyst: The user editing this relationship.
        :type analyst: str
        :returns: dict with keys "success" (boolean) and "message" (str)
        """

        return self._modify_relationship(rel_item=rel_item, rel_id=rel_id,
                             type_=type_, rel_type=rel_type,
                             rel_date=rel_date, new_type=new_type,
                             modification="type", analyst=analyst)

    def edit_relationship_confidence(self, rel_item=None, rel_id=None,
                                     type_=None, rel_type=None, rel_date=None,
                                     new_confidence='unknown', analyst=None):
        """
        Modify a relationship type for a relationship to this top-level object.
        If rel_item is provided it will be used, otherwise rel_id and type_ must
        be provided.

        :param rel_item: The top-level object to relate to.
        :type rel_item: class which inherits from
                        :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        :param rel_id: The ObjectId of the top-level object to relate to.
        :type rel_id: str
        :param type_: The type of top-level object to relate to.
        :type type_: str
        :param rel_type: The type of relationship.
        :type rel_type: str
        :param rel_date: The date this relationship applies.
        :type rel_date: datetime.datetime
        :param new_confidence: The new confidence of the relationship.
        :type new_confidence: str
        :param analyst: The user editing this relationship.
        :type analyst: str
        :returns: dict with keys "success" (boolean) and "message" (str)
        """
        return self._modify_relationship(rel_item=rel_item, rel_id=rel_id,
                             type_=type_, rel_type=rel_type,
                             rel_date=rel_date, new_confidence=new_confidence,
                             modification="confidence", analyst=analyst)

    def edit_relationship_reason(self, rel_item=None, rel_id=None, type_=None,
                                 rel_type=None, rel_date=None, new_reason="N/A",
                                 analyst=None):
        """
        Modify a relationship type for a relationship to this top-level object.
        If rel_item is provided it will be used, otherwise rel_id and type_ must
        be provided.

        :param rel_item: The top-level object to relate to.
        :type rel_item: class which inherits from
                        :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        :param rel_id: The ObjectId of the top-level object to relate to.
        :type rel_id: str
        :param type_: The type of top-level object to relate to.
        :type type_: str
        :param rel_type: The type of relationship.
        :type rel_type: str
        :param rel_date: The date this relationship applies.
        :type rel_date: datetime.datetime
        :param new_confidence: The new confidence of the relationship.
        :type new_confidence: int
        :param analyst: The user editing this relationship.
        :type analyst: str
        :returns: dict with keys "success" (boolean) and "message" (str)
        """
        return self._modify_relationship(rel_item=rel_item, rel_id=rel_id,
                             type_=type_, rel_type=rel_type,
                             rel_date=rel_date, new_reason=new_reason,
                             modification="reason", analyst=analyst)

    def delete_relationship(self, rel_item=None, rel_id=None, type_=None, rel_type=None,
                            rel_date=None, analyst=None, *args, **kwargs):
        """
        Delete a relationship from a relationship to this top-level object.
        If rel_item is provided it will be used, otherwise rel_id and type_ must
        be provided.

        :param rel_item: The top-level object to remove relationship to.
        :type rel_item: class which inherits from
                        :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        :param rel_id: The ObjectId of the top-level object to relate to.
        :type rel_id: str
        :param type_: The type of top-level object to relate to.
        :type type_: str
        :param rel_type: The type of relationship.
        :type rel_type: str
        :param rel_date: The date this relationship applies.
        :type rel_date: datetime.datetime
        :param analyst: The user removing this relationship.
        :type analyst: str
        :returns: dict with keys "success" (boolean) and "message" (str)
        """

        return self._modify_relationship(rel_item=rel_item, rel_id=rel_id,
                             type_=type_, rel_type=rel_type,
                             rel_date=rel_date, analyst=analyst,
                             modification="delete")

    def delete_all_relationships(self, username=None):
        """
        Delete all relationships from this top-level object.

        :param username: The user deleting all of the relationships.
        :type username: str
        """

        for r in self.relationships[:]:
            if r.relationship_date:
                self.delete_relationship(rel_id=str(r.object_id),
                                         type_=r.rel_type,
                                         rel_type=r.relationship,
                                         rel_date=r.relationship_date,
                                         analyst=username)
            else:
                self.delete_relationship(rel_id=str(r.object_id),
                                         type_=r.rel_type,
                                         rel_type=r.relationship,
                                         analyst=username)

    def sort_relationships(self, username=None, meta=False):
        """
        Sort the relationships for inclusion in a template.

        :param username: The user requesting the relationships.
        :type username: str
        :param meta: Limit the results to only a subset of metadata.
        :type meta: boolean
        :returns: dict
        """

        if len(self.relationships) < 1:
            return {}
        rel_dict = dict((r.rel_type,[]) for r in self.relationships)
        query_dict = {
            'Actor': ('id', 'name', 'campaign'),
            'Backdoor': ('id', 'name', 'version', 'campaign'),
            'Campaign': ('id', 'name'),
            'Certificate': ('id', 'md5', 'filename', 'description', 'campaign'),
            'Domain': ('id', 'domain'),
            'Email': ('id', 'from_address', 'sender', 'subject', 'campaign'),
            'Event': ('id', 'title', 'event_type', 'description', 'campaign'),
            'Exploit': ('id', 'name', 'cve', 'campaign'),
            'Indicator': ('id', 'ind_type', 'value', 'campaign', 'actions'),
            'IP': ('id', 'ip', 'campaign'),
            'PCAP': ('id', 'md5', 'filename', 'description', 'campaign'),
            'RawData': ('id', 'title', 'data_type', 'tool', 'description',
                        'version', 'campaign'),
            'Sample': ('id',
                       'md5',
                       'filename',
                       'mimetype',
                       'size',
                       'campaign'),
            'Signature': ('id', 'title', 'data_type', 'description',
                        'version', 'campaign'),
            'Target': ('id', 'firstname', 'lastname', 'email_address', 'email_count'),
        }
        rel_dict['Other'] = 0
        rel_dict['Count'] = len(self.relationships)
        if not meta:
            for r in self.relationships:
                rd = r.to_dict()
                rel_dict[rd['type']].append(rd)
            return rel_dict
        elif username:
            user_source_access = user_sources(username)
            for r in self.relationships:
                rd = r.to_dict()
                obj_class = class_from_type(rd['type'])
                # TODO: these should be limited to the fields above, or at
                # least exclude larger fields that we don't need.
                fields = query_dict.get(rd['type'])
                if r.rel_type not in ["Campaign", "Target"]:
                    obj = obj_class.objects(id=rd['value'],
                            source__name__in=user_source_access).only(*fields).first()
                else:
                    obj = obj_class.objects(id=rd['value']).only(*fields).first()
                if obj:
                    # we can't add and remove attributes on the class
                    # so convert it to a dict that we can manipulate.
                    result = obj.to_dict()
                    if "_id" in result:
                        result["id"] = result["_id"]
                    if "type" in result:
                        result["ind_type"] = result["type"]
                        del result["type"]
                    if "value" in result:
                        result["ind_value"] = result["value"]
                        del result["value"]
                    # turn this relationship into a dict so we can update
                    # it with the object information
                    rd.update(result)
                    rel_dict[rd['type']].append(rd)
                else:
                    rel_dict['Other'] += 1
            return rel_dict
        else:
            return {}

    def get_relationship_objects(self, username=None, sources=None):
        """
        Return the top-level objects this top-level object is related to.

        :param username: The user requesting these top-level objects.
        :type username: str
        :param sources: The user's source access list to limit by.
        :type sources: list
        :returns: list
        """

        results = []
        if not username:
            return results
        if not hasattr(self, 'relationships'):
            return results
        if not sources:
            sources = user_sources(username)
        for r in self.relationships:
            rd = r.to_dict()
            obj_class = class_from_type(rd['type'])
            if r.rel_type not in ["Campaign", "Target"]:
                obj = obj_class.objects(id=rd['value'],
                        source__name__in=sources).first()
            else:
                obj = obj_class.objects(id=rd['value']).first()
            if obj:
                results.append(obj)
        return results

    def add_releasability(self, source_item=None, analyst=None, *args, **kwargs):
        """
        Add a source as releasable for this top-level object.

        :param source_item: The source to allow releasability for.
        :type source_item: dict or
                           :class:`crits.core.crits_mongoengine.Releasability`
        :param analyst: The user marking this as releasable.
        :type analyst: str
        """

        if isinstance(source_item, Releasability):
            rels = self.releasability
            for r in rels:
                if r.name == source_item.name:
                    break
            else:
                if analyst:
                    source_item.analyst = analyst
                self.releasability.append(source_item)
        elif isinstance(source_item, dict):
            rels = self.releasability
            for r in rels:
                if r.name == source_item['name']:
                    break
            else:
                if analyst:
                    source_item['analyst'] = analyst
                self.releasability.append(Releasability(**source_item))
        else:
            rel = Releasability(**kwargs)
            if analyst:
                rel.analyst = analyst
            rels = self.releasability
            for r in rels:
                if r.name == rel.name:
                    break
            else:
                self.releasability.append(rel)

    def add_releasability_instance(self, name=None, instance=None, *args, **kwargs):
        """
        Add an instance of releasing this top-level object to a source.

        :param name: The name of the source that received the data.
        :type name: str
        :param instance: The instance of releasability.
        :type instance:
            :class:`crits.core.crits_mongoengine.Releasability.ReleaseInstance`
        """

        if isinstance(instance, Releasability.ReleaseInstance):
            for r in self.releasability:
                if r.name == name:
                    r.instances.append(instance)

    def remove_releasability(self, name=None, *args, **kwargs):
        """
        Remove a source as releasable for this top-level object.

        :param name: The name of the source to remove from releasability.
        :type name: str
        """

        if isinstance(name, basestring):
            for r in self.releasability:
                if r.name == name and len(r.instances) == 0:
                    self.releasability.remove(r)
                    break

    def remove_releasability_instance(self, name=None, date=None, *args, **kwargs):
        """
        Remove an instance of releasing this top-level object to a source.

        :param name: The name of the source.
        :type name: str
        :param date: The date of the instance to remove.
        :type date: datetime.datetime
        """

        if not isinstance(date, datetime.datetime):
            date = parse(date, fuzzy=True)
        for r in self.releasability:
            if r.name == name:
                for ri in r.instances:
                    if ri.date == date:
                        r.instances.remove(ri)

    def sanitize_relationships(self, username=None, sources=None):
        """
        Sanitize the relationships list down to only what the user can see based
        on source access.

        :param username: The user to sanitize for.
        :type username: str
        :param source: The user's source list.
        :type source: list
        """

        if username:
            if not sources:
                sources = user_sources(username)
            final_rels = []
            for r in self.relationships:
                rd = r.to_dict()
                obj_class = class_from_type(rd['type'])
                if r.rel_type not in ["Campaign", "Target"]:
                    obj = obj_class.objects(id=rd['value'],
                            source__name__in=sources).only('id').first()
                else:
                    obj = obj_class.objects(id=rd['value']).only('id').first()
                if obj:
                    final_rels.append(r)
            self.relationships = final_rels

    def sanitize_releasability(self, username=None, sources=None):
        """
        Sanitize releasability list down to only what the user can see based
        on source access.

        :param username: The user to sanitize for.
        :type username: str
        :param source: The user's source list.
        :type source: list
        """

        if username:
            if not sources:
                sources = user_sources(username)
            # use slice to modify in place in case any code is referencing
            # the source already will reflect the changes as well
            self.releasability[:] = [r for r in self.releasability if r.name in sources]


    def sanitize(self, username=None, sources=None, rels=True):
        """
        Sanitize this top-level object down to only what the user can see based
        on source access.

        :param username: The user to sanitize for.
        :type username: str
        :param source: The user's source list.
        :type source: list
        :param rels: Whether or not to sanitize relationships.
        :type rels: boolean
        """

        if username:
            if not sources:
                sources = user_sources(username)
            if hasattr(self, 'source'):
                self.sanitize_sources(username, sources)
            if hasattr(self, 'releasability'):
                self.sanitize_releasability(username, sources)
            if rels:
                if hasattr(self, 'relationships'):
                    self.sanitize_relationships(username, sources)


    def get_campaign_names(self):
        """
        Get the campaigns associated with this top-level object as a list of
        names.

        :returns: list
        """

        return [obj['name'] for obj in self._data['campaign']]


    def get_analysis_results(self):
        """
        Get analysis results for this TLO.

        :returns: list
        """

        from crits.services.analysis_result import AnalysisResult

        return AnalysisResult.objects(object_id=str(self.id))

    def get_details_url(self):
        """
        Generic function that generates a details url for a
        :class:`crits.core.crits_mongoengine.CritsBaseAttributes` object.
        """

        mapper = self._meta.get('jtable_opts')
        if mapper is not None:
            details_url = mapper['details_url']
            details_url_key = mapper['details_url_key']

            try:
                return reverse(details_url, args=(unicode(self[details_url_key]),))
            except Exception:
                return None
        else:
            return None


class CommonAccess(BaseDocument):
    """
    ACL for common TLO content.
    """

    # Basics
    read = BooleanField(default=False)
    write = BooleanField(default=False)
    delete = BooleanField(default=False)
    download = BooleanField(default=False)

    description_read = BooleanField(default=False)
    description_edit = BooleanField(default=False)

    #Actions List
    actions_read = BooleanField(default=False)
    actions_add = BooleanField(default=False)
    actions_edit = BooleanField(default=False)
    actions_delete = BooleanField(default=False)

    # Bucket List
    bucketlist_read = BooleanField(default=False)
    bucketlist_edit = BooleanField(default=False)

    # Campaigns
    campaigns_read = BooleanField(default=False)
    campaigns_add = BooleanField(default=False)
    campaigns_edit = BooleanField(default=False)
    campaigns_delete = BooleanField(default=False)

    # Comments
    comments_read = BooleanField(default=False)
    comments_add = BooleanField(default=False)
    comments_edit = BooleanField(default=False)
    comments_delete = BooleanField(default=False)

    # Locations
    locations_read = BooleanField(default=False)
    locations_add = BooleanField(default=False)
    locations_edit = BooleanField(default=False)
    locations_delete = BooleanField(default=False)

    # Objects
    objects_read = BooleanField(default=False)
    objects_add = BooleanField(default=False)
    objects_edit = BooleanField(default=False)
    objects_delete = BooleanField(default=False)

    # Relationships
    relationships_read = BooleanField(default=False)
    relationships_add = BooleanField(default=False)
    relationships_edit = BooleanField(default=False)
    relationships_delete = BooleanField(default=False)

    # Releasability
    releasability_read = BooleanField(default=False)
    releasability_add = BooleanField(default=False)
    releasability_delete = BooleanField(default=False)

    # Screenshots
    screenshots_read = BooleanField(default=False)
    screenshots_add = BooleanField(default=False)
    screenshots_delete = BooleanField(default=False)

    # Sectors
    sectors_read = BooleanField(default=False)
    sectors_edit = BooleanField(default=False)

    # Services
    services_read = BooleanField(default=False)
    services_execute = BooleanField(default=False)

    # Sources
    sources_read = BooleanField(default=False)
    sources_add = BooleanField(default=False)
    sources_edit = BooleanField(default=False)
    sources_delete = BooleanField(default=False)

    # Status
    status_read = BooleanField(default=False)
    status_edit = BooleanField(default=False)

    # Tickets
    tickets_read = BooleanField(default=False)
    tickets_add = BooleanField(default=False)
    tickets_edit = BooleanField(default=False)
    tickets_delete = BooleanField(default=False)


def merge(self, arg_dict=None, overwrite=False, **kwargs):
    """
    Merge attributes into self.

    If arg_dict is supplied, it should be either a dictionary or
    another object that can be iterated over like a dictionary's
    iteritems (e.g., a list of two-tuples).

    If arg_dict is not supplied, attributes can also be defined with
    named keyword arguments; attributes supplied as keyword arguments
    will be ignored if arg_dict is not None.

    If overwrite is True, any attributes passed to merge will be
    assigned to the object, regardless of whether those attributes
    already exist. If overwrite is False, pre-existing attributes
    will be preserved.
    """

    if not arg_dict:
        arg_dict = kwargs
    if isinstance(arg_dict, dict):
        iterator = arg_dict.iteritems()
    else:
        iterator = arg_dict

    if overwrite:
        for k,v in iterator:
            if k != '_id' and k != 'schema_version':
                self.__setattr__(k, v)
    else:
        for k,v in iterator:
            check = getattr(self, k, None)
            if not check:
                self.__setattr__(k, v)
            elif hasattr(self, '_meta') and 'duplicate_attrs' in self._meta:
                self._meta['duplicate_attrs'].append((k,v))

# this is a duplicate of the function in data_tools to prevent
# circular imports. long term the one in data_tools might go
# away as most json conversion will happen using .to_json()
# on the object.
def json_handler(obj):
    """
    Handles converting datetimes and Mongo ObjectIds to string.

    Usage: json.dumps(..., default=json_handler)
    """
    if isinstance(obj, datetime.datetime):
        return datetime.datetime.strftime(obj, settings.PY_DATETIME_FORMAT)
    elif isinstance(obj, ObjectId):
        return str(obj)

def create_embedded_source(name, source_instance=None, date=None,
                           reference='', method='', tlp=None,
                           needs_tlp=True, analyst=None):
    """
    Create an EmbeddedSource object. If source_instance is provided it will be
    used, otherwise date, reference, and method will be used.

    :param name: The name of the source.
    :type name: str
    :param source_instance: An instance of this source.
    :type source_instance:
        :class:`crits.core.crits_mongoengine.EmbeddedSource.SourceInstance`
    :param date: The date for the source instance.
    :type date: datetime.datetime
    :param method: The method for this source instance.
    :type method: str
    :param reference: The reference for this source instance.
    :type reference: str
    :param tlp: The TLP for this source instance.
    :type tlp: str
    :param needs_tlp: If this source needs a TLP (object sources don't yet).
    :type needs_tlp: bool
    :param analyst: The user creating this embedded source.
    :type analyst: str
    :returns: None, :class:`crits.core.crits_mongoengine.EmbeddedSource`
    """

    if tlp not in ('white', 'green', 'amber', 'red', None):
        return None

    if isinstance(name, basestring):
        s = EmbeddedSource()
        s.name = name
        if isinstance(source_instance, EmbeddedSource.SourceInstance):
            s.instances = [source_instance]
        else:
            if not date:
                date = datetime.datetime.now()
            i = EmbeddedSource.SourceInstance()
            i.date = date
            i.reference = reference
            i.method = method
            if needs_tlp:
                if not tlp:
                    return None
                i.tlp = tlp
            i.analyst = analyst
            s.instances = [i]
        return s
    else:
        return None
