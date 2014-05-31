from django.conf import settings
from mongoengine import Document, StringField, IntField

from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument

class Division(CritsDocument, CritsSchemaDocument, Document):
    """
    Division class.
    """

    meta = {
        "collection": settings.COL_DIVISION_DATA,
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
