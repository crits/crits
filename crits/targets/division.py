from django.conf import settings
try:
	from django_mongoengine import Document
except ImportError:
	from mongoengine import Document

from mongoengine import StringField, IntField

from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument

class Division(CritsDocument, CritsSchemaDocument, Document):
    """
    Division class.
    """

    meta = {
        "collection": settings.COL_DIVISION_DATA,
        "auto_create_index": False,
        "crits_type": 'Division',
        "latest_schema_version": 1,
        "schema_doc": {
            'division': 'The name of the division',
            'email_count': ('The number of emails with to addresses for targets'
                            ' in this division. Added by MapReduce')
        },
    }

    division = StringField()
    email_count = IntField()

    def migrate(self):
        pass
