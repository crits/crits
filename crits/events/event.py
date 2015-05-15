import uuid

from mongoengine import Document, StringField, UUIDField
from django.conf import settings

from crits.core.crits_mongoengine import CritsSchemaDocument, CritsBaseAttributes
from crits.core.crits_mongoengine import CritsDocument, CritsSourceDocument
from crits.events.migrate import migrate_event

class UnreleasableEventError(Exception):
    """
    Exception for attempting to release an event relationship that is
    unreleasable.
    """

    def __init__(self, value, **kwargs):
        self.message = "Relationship %s cannot be released to the event's \
releasability list." % value
        super(UnreleasableEventError, self).__init__(**kwargs)

    def __str__(self):
        return repr(self.message)

class Event(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    Event class.
    """

    meta = {
        "collection": settings.COL_EVENTS,
        "crits_type": 'Event',
        "latest_schema_version": 3,
        "schema_doc": {
            'title': 'Title of this event',
            'event_id': 'Unique event ID',
            'event_type': 'Type of event based on Event Type options',
            'description': 'Description of the event',
            'source': ('List [] of sources who provided information about this'
                ' event')
        },
        "jtable_opts": {
                         'details_url': 'crits.events.views.view_event',
                         'details_url_key': 'id',
                         'default_sort': "created DESC",
                         'searchurl': 'crits.events.views.events_listing',
                         'fields': [ "title", "event_type", "created",
                                     "source", "campaign", "status", "id"],
                         'jtopts_fields': [ "details",
                                            "title",
                                            "event_type",
                                            "created",
                                            "source",
                                            "campaign",
                                            "status",
                                            "favorite",
                                            "id"],
                         'hidden_fields': [],
                         'linked_fields': ["source", "campaign", "event_type"],
                         'details_link': 'details',
                         'no_sort': ['details']
                       }

    }

    title = StringField(required=True)
    event_type = StringField(required=True)
    # description also exists in CritsBaseAttributes, but this one is required.
    description = StringField(required=True)
    event_id = UUIDField(binary=True, required=True, default=uuid.uuid4)

    def set_event_type(self, event_type):
        """
        Set the Event Type.

        :param event_type: The event type to set (must exist in DB).
        :type event_type: str
        """

        e = EventType.objects(name=event_type).first()
        if e:
            self.event_type = event_type

    def migrate(self):
        """
        Migrate to the latest schema version.
        """

        migrate_event(self)


class EventType(CritsDocument, CritsSchemaDocument, Document):
    """
    Event Type class.
    """

    meta = {
        "collection": settings.COL_EVENT_TYPES,
        "crits_type": 'EventType',
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'The name of this Type',
            'active': 'Enabled in the UI (on/off)'
        },
    }

    name = StringField()
    active = StringField()
