import datetime
import uuid

from dateutil.parser import parse
from mongoengine import Document, StringField, IntField, EmbeddedDocument
from mongoengine import ListField, EmbeddedDocumentField, UUIDField
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsSourceDocument
from crits.core.crits_mongoengine import CritsDocumentFormatter
from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument
from crits.core.fields import CritsDateTimeField, getFileField

from cybox.objects.artifact_object import Artifact, Base64Encoding
from cybox.core import Observable


class DisassemblyType(CritsDocument, CritsSchemaDocument, Document):
    """
    Disassembly type class.
    """

    meta = {
        "collection": settings.COL_DISASSEMBLY_TYPES,
        "crits_type": 'DisassemblyType',
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'The name of this disassembly type',
            'active': 'Enabled in the UI (on/off)'
        },
    }

    name = StringField()
    active = StringField(default="on")


class EmbeddedTool(EmbeddedDocument, CritsDocumentFormatter):
    """
    Disassembly Tool class.
    """

    name = StringField()
    version = StringField()
    details = StringField()


class Disassembly(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    Disassembly class.
    """

    meta = {
        "collection": settings.COL_DISASSEMBLY,
        "crits_type": 'Disassembly',
        "latest_schema_version": 1,
        "schema_doc": {
        },
        "jtable_opts": {
                         'details_url': 'crits.disassembly.views.disassembly_details',
                         'details_url_key': 'id',
                         'default_sort': "modified DESC",
                         'searchurl': 'crits.disassembly.views.disassembly_listing',
                         'fields': [ "title", "data_type", "version",
                                     "modified", "source", "campaign",
                                     "id", "status"],
                         'jtopts_fields': [ "details",
                                            "title",
                                            "data_type",
                                            "version",
                                            "modified",
                                            "source",
                                            "campaign",
                                            "status",
                                            "favorite",
                                            "id"],
                         'hidden_fields': [],
                         'linked_fields': ["source", "campaign"],
                         'details_link': 'details',
                         'no_sort': ['details']
                       }
    }

    data_type = StringField()
    description = StringField()
    filedata = getFileField(collection_name=settings.COL_DISASSEMBLY)
    link_id = UUIDField(binary=True, required=True, default=uuid.uuid4())
    md5 = StringField()
    title = StringField()
    tool = EmbeddedDocumentField(EmbeddedTool)
    version = IntField(default=0)

    def migrate(self):
        """
        Migrate to the latest schema version.
        """

        pass

    def add_file_data(self, file_data):
        """
        Add filedata to Disassembly.

        :param file_data: The disassembly data to add.
        :type file_data: str
        """

        self._generate_file_metadata(file_data)
        self.filedata = file_data

    def add_file_obj(self, file_obj):
        """
        Add fileobj to Disassembly.

        :param file_obj: The disassembly file object to add.
        :type file_obj: file handle
        """

        data = file_obj.read()
        self._generate_file_metadata(data)
        self.data = data

    def _generate_file_metadata(self, data):
        """
        Generate metadata from the disassembly data.
        Uses the data to generate an MD5.

        :param data: The data to generate metadata from.
        """

        from hashlib import md5
        if not self.md5:
            self.md5 = md5(data).hexdigest()

    def add_tool(self, name=None, version=None, details=None):
        """
        Add a tool to Disassembly.

        :param name: The name of the tool used to generate the disassembly.
        :type name: str
        :param version: The version number of the tool.
        :type version: str
        :param details: Details about the tool.
        :type details: str
        """

        if name:
            et = EmbeddedTool(name=name,
                            version=version,
                            details=details)
            self.tool = et


    def to_cybox_observable(self):
        """
            Convert a Disassembly to a CybOX Observables.
            Returns a tuple of (CybOX object, releasability list).

            To get the cybox object as xml or json, call to_xml() or
            to_json(), respectively, on the resulting CybOX object.
        """
        obj = Artifact(self.data, Artifact.TYPE_FILE)
        obj.packaging.append(Base64Encoding())
        obs = Observable(obj)
        obs.description = self.description
        return ([obs], self.releasability)

    @classmethod
    def from_cybox(cls, cybox_obs, source):
        """
        Convert a Cybox DefinedObject to a MongoEngine Indicator object.

        :param cybox_obs: The cybox object to create the indicator from.
        :type cybox_obs: :class:`cybox.core.Observable``
        :param source: The source list for the Indicator.
        :type source: list
        :returns: :class:`crits.indicators.indicator.Indicator`
        """
        cybox_object = cybox_obs.object_.properties
        disassembly = cls(source=source)
        disassembly.add_file_data(cybox_object.data)
        db_obj = Disassembly.objects(md5=disassembly.md5).first()
        if db_obj:
            return db_obj
        return disassembly

