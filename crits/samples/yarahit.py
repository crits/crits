from mongoengine import Document, StringField, IntField
from django.conf import settings

from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument


class YaraHit(CritsDocument, CritsSchemaDocument, Document):
    """
    Yara Hit class.
    """

    meta = {
        "collection": settings.COL_YARAHITS,
        "crits_type": "YaraHit",
        "latest_schema_version": 1,
        "schema_doc": {
            'engine': 'The Yara engine that ran',
            'result': 'The yara rule that hit',
            'sample_count': ('The number of samples that triggered this rule. '
                             'Added by MapReduce'),
            'version': 'The version of yara signatures that were used',
        }
    }

    engine = StringField()
    result = StringField()
    sample_count = IntField()
    version = StringField()
