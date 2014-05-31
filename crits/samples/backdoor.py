from mongoengine import Document, IntField, StringField
from django.conf import settings

from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument


class Backdoor(CritsDocument, CritsSchemaDocument, Document):
    """
    Backdoor class.
    """

    meta = {
        "crits_type": "Backdoor",
        "collection": settings.COL_BACKDOOR_DETAILS,
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'Name of the backdoor',
            'active': 'Enabled in the UI (on/off)',
            'sample_count': ('Number of samples with this backdoor. Added by'
                             ' MapReduce')
        }
    }

    name = StringField()
    #TODO: this could be a boolean field if we migrate
    active = StringField(default="on")
    sample_count = IntField(default=0)

    def increment_count(self):
        """
        Increment count of backdoors instances in CRITs.
        """

        self.sample_count += 1

    def decrement_count(self):
        """
        Decrement count of backdoors instances in CRITs.
        """

        self.sample_count -= 1
