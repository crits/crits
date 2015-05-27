import datetime
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

    def stix_description(self):
        return self.description

    def stix_intent(self):
        return self.event_type

    def stix_title(self):
        return self.title

    def to_stix_incident(self):
        """
        Creates a STIX Incident object from a CRITs Event.

        Returns the STIX Incident and the original CRITs Event's
        releasability list.
        """
        from stix.incident import Incident
        inc = Incident(title=self.title, description=self.description)

        return (inc, self.releasability)

    @classmethod
    def from_stix(cls, stix_package):
        """
        Converts a stix_package to a CRITs Event.

        :param stix_package: A stix package.
        :type stix_package: :class:`stix.core.STIXPackage`
        :returns: None, :class:`crits.events.event.Event'
        """

        from stix.common import StructuredText
        from stix.core import STIXPackage, STIXHeader

        if isinstance(stix_package, STIXPackage):
            stix_header = stix_package.stix_header
            stix_id = stix_package.id_
            event = cls()
            event.title = "STIX Document %s" % stix_id
            event.event_type = "Collective Threat Intelligence"
            event.description = str(datetime.datetime.now())
            eid = stix_package.id_
            try:
                uuid.UUID(eid)
            except ValueError:
                # The STIX package ID attribute is not a valid UUID
                # so make one up.
                eid = uuid.uuid4() # XXX: Log this somewhere?
            event.event_id = eid
            if isinstance(stix_header, STIXHeader):
                if stix_header.title:
                    event.title = stix_header.title
                #if stix_header.package_intents:
                # package_intents are optional in the STIX Spec.. So we check for the attribute being present
                # rather than the original check which causes an exception
                if hasattr(stix_header,'package_intents'):
                    event.event_type = str(stix_header.package_intents[0])
                description = stix_header.description
                if isinstance(description, StructuredText):
                    try:
                        event.description = description.to_dict()
                    except:
                        pass
            return event
        else:
            return None

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
