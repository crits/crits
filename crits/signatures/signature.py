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
from crits.signatures.migrate import migrate_signature


class SignatureType(CritsDocument, CritsSchemaDocument, Document):
    """
    Signature type class.
    """

    meta = {
        "collection": settings.COL_SIGNATURE_TYPES,
        "crits_type": 'SignatureType',
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
    Signature highlight comment class.
    """

    date = CritsDateTimeField(default=datetime.datetime.now)
    line_date = CritsDateTimeField()
    analyst = StringField()
    line = IntField()
    line_data = StringField()
    comment = StringField()


class EmbeddedInline(EmbeddedDocument, CritsDocumentFormatter):
    """
    Signature Inline comment class.
    """

    date = CritsDateTimeField(default=datetime.datetime.now)
    analyst = StringField()
    line = IntField()
    comment = StringField()
    counter = IntField()


class Signature(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    Signature class.
    """

    meta = {
        "collection": settings.COL_SIGNATURES,
        "crits_type": 'Signature',
        "latest_schema_version": 2,
        "schema_doc": {
        },
        "jtable_opts": {
                         'details_url': 'crits.signatures.views.signature_detail',
                         'details_url_key': 'id',
                         'default_sort': "modified DESC",
                         'searchurl': 'crits.signatures.views.signature_listing',
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
    version = IntField()

    def migrate(self):
        """
        Migrate to the latest schema version.
        """

        migrate_signature(self)

    def _generate_file_metadata(self, data):
        """
        Generate metadata from the signature. Uses the data to generate an MD5.

        :param data: The data to generate metadata from.
        """

        from hashlib import md5
        if not self.md5:
            self.md5 = md5(data).hexdigest()

    def add_inline_comment(self, comment, line_num, analyst):
        """
        Add an inline comment for Signature.

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
        Highlight a specific line of the Signature.

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
        Remove highlight from a specific line of the Signature.

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