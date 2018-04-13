import datetime

try:
	from django_mongoengine import Document
except ImportError:
	from mongoengine import Document

from mongoengine import StringField, ObjectIdField
from django.conf import settings

from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument
from crits.core.fields import CritsDateTimeField


class AuditLog(CritsDocument, CritsSchemaDocument, Document):
    """
    Audit Log Class
    """
    meta = {
        "collection": settings.COL_AUDIT_LOG,
        "auto_create_index": False,
        "allow_inheritance": False,
        "crits_type": "AuditLog",
        "latest_schema_version": 1,
        "schema_doc": {
            'value': 'Value of the audit log entry',
            'user': 'User the entry is about.',
            'date': 'Date of the entry',
            'type': 'Type of the audit entry',
            'method': 'Method of the audit entry'
        }
    }

    value = StringField()
    user = StringField()
    date = CritsDateTimeField(default=datetime.datetime.now)
    target_type = StringField(db_field='type')
    target_id = ObjectIdField()
    method = StringField()
