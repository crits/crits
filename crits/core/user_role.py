try:
	from django_mongoengine import Document
except ImportError:
	from mongoengine import Document

from mongoengine import StringField
from django.conf import settings

from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument

class UserRole(CritsDocument, CritsSchemaDocument, Document):
    """
    User Role object.
    """

    meta = {
        "collection": settings.COL_USER_ROLES,
        "auto_create_index": False,
        "crits_type": 'UserRole',
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'Name of the role',
            'active': 'Enabled in the UI (on/off)'
        },
    }

    name = StringField()
    active = StringField(default="on")
