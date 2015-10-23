import uuid

from mongoengine import Document, StringField, IntField
from mongoengine import UUIDField
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsSourceDocument
from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument


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

class Signature(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    Signature class.
    """

    meta = {
        "collection": settings.COL_SIGNATURES,
        "crits_type": 'Signature',
        "latest_schema_version": 1,
        "schema_doc": {
        },
        "jtable_opts": {
                         'details_url': 'crits.signatures.views.signature_detail',
                         'details_url_key': 'id',
                         'default_sort': "modified DESC",
                         'searchurl': 'crits.signatures.views.signatures_listing',
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
    link_id = UUIDField(binary=True, required=True, default=uuid.uuid4)
    md5 = StringField()
    title = StringField()
    version = IntField()

    def _generate_file_metadata(self, data):
        """
        Generate metadata from the signature. Uses the data to generate an MD5.

        :param data: The data to generate metadata from.
        """

        from hashlib import md5
        if not self.md5:
            self.md5 = md5(data).hexdigest()