import datetime

try:
	from django_mongoengine import Document
except ImportError:
	from mongoengine import Document

from mongoengine import ObjectIdField, StringField, ListField
from django.conf import settings

from crits.core.fields import CritsDateTimeField
from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument


class Notification(CritsDocument, CritsSchemaDocument, Document):
    """
    Notification Class.
    """

    meta = {
        "collection": settings.COL_NOTIFICATIONS,
        "auto_create_index": False,
        "crits_type": "Notification",
        "latest_schema_version": 1,
        "schema_doc": {
            'notification': 'The notification body',
            'notification_type': 'The type of notification, e.g. alert, error',
            'header': 'The notification header, optional',
            'link_url': 'A link URL for the header, optional',
            'status': 'New/Processed - used to determine whether or not to notify',
            'obj_type': 'The type of the object this notification is for',
            'obj_id': 'The MongoDB ObjectId for the object this notification is for',
            'created': 'ISODate when this notification was made',
            'users': 'List [] of users for this notification',
            'analyst': 'The analyst, if any, that made this notification',
        }
    }
    # This is not a date field!
    # It exists to provide default values for created and edit_date
    date = datetime.datetime.now()

    analyst = StringField()
    notification = StringField()
    notification_type = StringField()
    header = StringField()
    created = CritsDateTimeField(default=date, db_field="date")
    obj_id = ObjectIdField()
    obj_type = StringField()
    status = StringField(default="new")
    link_url = StringField()
    users = ListField(StringField())

    def set_status(self, status):
        """
        Set the status of the notification.

        :param status: The status ("new", "processed").
        :type status: str
        """

        if status in ("new", "processed"):
            self.status = status
