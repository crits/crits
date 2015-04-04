import datetime
import uuid

from dateutil.parser import parse
from mongoengine import Document, StringField, IntField, EmbeddedDocument
from mongoengine import ListField, EmbeddedDocumentField, UUIDField
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsSourceDocument
from crits.core.crits_mongoengine import CritsDocumentFormatter
from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument
from crits.core.fields import CritsDateTimeField
from crits.raw_data.migrate import migrate_raw_data

from cybox.objects.artifact_object import Artifact, Base64Encoding
from cybox.core import Observable


class RawDataType(CritsDocument, CritsSchemaDocument, Document):
    """
    Raw Data type class.
    """

    meta = {
        "collection": settings.COL_RAW_DATA_TYPES,
        "crits_type": 'RawDataType',
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'The name of this data type',
            'active': 'Enabled in the UI (on/off)'
        },
    }

    name = StringField()
    active = StringField(default="on")

class EmbeddedHighlight(EmbeddedDocument, CritsDocumentFormatter):
    """
    Raw Data highlight comment class.
    """

    date = CritsDateTimeField(default=datetime.datetime.now)
    line_date = CritsDateTimeField()
    analyst = StringField()
    line = IntField()
    line_data = StringField()
    comment = StringField()


class EmbeddedInline(EmbeddedDocument, CritsDocumentFormatter):
    """
    Raw Data Inline comment class.
    """

    date = CritsDateTimeField(default=datetime.datetime.now)
    analyst = StringField()
    line = IntField()
    comment = StringField()
    counter = IntField()


class EmbeddedTool(EmbeddedDocument, CritsDocumentFormatter):
    """
    Raw Data Tool class.
    """

    name = StringField()
    version = StringField()
    details = StringField()


class RawData(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    Raw Data class.
    """

    meta = {
        "collection": settings.COL_RAW_DATA,
        "crits_type": 'RawData',
        "latest_schema_version": 2,
        "schema_doc": {
        },
        "jtable_opts": {
                         'details_url': 'crits.raw_data.views.raw_data_details',
                         'details_url_key': 'id',
                         'default_sort': "modified DESC",
                         'searchurl': 'crits.raw_data.views.raw_data_listing',
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
    data = StringField()
    highlights = ListField(EmbeddedDocumentField(EmbeddedHighlight))
    inlines = ListField(EmbeddedDocumentField(EmbeddedInline))
    link_id = UUIDField(binary=True, required=True, default=uuid.uuid4)
    md5 = StringField()
    title = StringField()
    tool = EmbeddedDocumentField(EmbeddedTool)
    version = IntField()

    def migrate(self):
        """
        Migrate to the latest schema version.
        """

        migrate_raw_data(self)

    def add_file_data(self, file_data):
        """
        Add filedata to RawData.

        :param file_data: The raw data to add.
        :type file_data: str
        """

        self._generate_file_metadata(file_data)
        self.data = file_data

    def add_file_obj(self, file_obj):
        """
        Add filedata to RawData.

        :param file_data: The raw data to add.
        :type file_data: file handle
        """

        data = file_obj.read()
        self._generate_file_metadata(data)
        self.data = data

    def _generate_file_metadata(self, data):
        """
        Generate metadata from the raw data. Uses the data to generate an MD5.

        :param data: The data to generate metadata from.
        """

        from hashlib import md5
        if not self.md5:
            self.md5 = md5(data).hexdigest()

    def add_tool(self, name=None, version=None, details=None):
        """
        Add a tool to RawData.

        :param name: The name of the tool used to generate/acquire the raw data.
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

    def add_inline_comment(self, comment, line_num, analyst):
        """
        Add an inline comment for RawData.

        :param comment: The comment to add.
        :type comment: str
        :param line_num: The line number this comment is associated with.
        :type line_Num: int
        :param analyst: The user making the comment.
        :type analyst: str
        """

        if comment:
            ei = EmbeddedInline(line=line_num,
                                comment=comment,
                                analyst=analyst)
            c = 1
            for i in self.inlines:
                if i.line == int(line_num) and i.counter >= c:
                    c = i.counter + 1
            ei.counter = c
            self.inlines.append(ei)

    def add_highlight(self, line_num, line_data, analyst):
        """
        Highlight a specific line of the RawData.

        :param line_num: The line number being highlighted.
        :type line_num: str
        :param line_data: The data on that line.
        :type line_data: str
        :param analyst: The user highlighting the line.
        :type analyst: str
        """

        eh = EmbeddedHighlight(line=line_num,
                                line_data=line_data,
                                analyst=analyst)
        # determine line date
        try:
            pd = parse(line_data, fuzzy=True)
            if pd:
                eh.line_date = pd
        except:
            eh.line_date = datetime.datetime.now()
        self.highlights.append(eh)

    def remove_highlight(self, line_num, analyst):
        """
        Remove highlight from a specific line of the RawData.

        :param line_num: The line number being unhighlighted.
        :type line_num: str
        :param analyst: The user unhighlighting the line.
        :type analyst: str
        """

        highlights = []
        for h in self.highlights:
            if h.line == int(line_num) and h.analyst == analyst:
                continue
            else:
                highlights.append(h)
        self.highlights = highlights

    def to_cybox_observable(self):
        """
            Convert a RawData to a CybOX Observables.
            Returns a tuple of (CybOX object, releasability list).

            To get the cybox object as xml or json, call to_xml() or
            to_json(), respectively, on the resulting CybOX object.
        """
        obj = Artifact(self.data.encode('utf-8'), Artifact.TYPE_FILE)
        obj.packaging.append(Base64Encoding())
        obs = Observable(obj)
        obs.description = self.description
        return ([obs], self.releasability)

    @classmethod
    def from_cybox(cls, cybox_obs):
        """
        Convert a Cybox DefinedObject to a MongoEngine RawData object.

        :param cybox_obs: The cybox object to create the RawData from.
        :type cybox_obs: :class:`cybox.core.Observable``
        :returns: :class:`crits.raw_data.raw_data.RawData`
        """
        cybox_object = cybox_obs.object_.properties
        rawdata = cls()
        rawdata.add_file_data(cybox_object.data)
        db_obj = RawData.objects(md5=rawdata.md5).first()
        if db_obj:
            return db_obj
        return rawdata
