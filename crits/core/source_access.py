from mongoengine import Document, IntField, StringField
from django.conf import settings

from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument


class SourceAccess(CritsDocument, CritsSchemaDocument, Document):
    """
    Source Access class.
    """

    meta = {
        "crits_type": "SourceAccess",
        "collection": settings.COL_SOURCE_ACCESS,
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'Name of the source',
            'active': 'Enabled in the UI (on/off)',
            'sample_count': 'Number of samples with this source.'
        }
    }

    name = StringField()
    #TODO: this could be a boolean field if we migrate
    active = StringField(default="on")
    sample_count = IntField(default=0)
