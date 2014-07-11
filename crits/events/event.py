import datetime
import uuid

from mongoengine import Document, StringField, UUIDField
from django.conf import settings

from crits.core.crits_mongoengine import CritsSchemaDocument, CritsBaseAttributes
from crits.core.crits_mongoengine import CritsDocument, CritsSourceDocument
from crits.core.user_tools import user_sources
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
        "latest_schema_version": 2,
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
    description = StringField(required=True)
    event_id = UUIDField(binary=True, required=True, default=uuid.uuid4())

    def set_event_type(self, event_type):
        """
        Set the Event Type.

        :param event_type: The event type to set (must exist in DB).
        :type event_type: str
        """

        e = EventType.objects(name=event_type).first()
        if e:
            self.event_type = event_type

    def to_stix(self, username=None):
        """
        Converts a CRITs event to a STIX document.

        The resulting document includes all related emails, samples, and
        indicators converted to CybOX Observable objects.
        Returns the STIX document and releasability constraints.

        (NOTE: the following statement is untrue until the
        releasability checking is finished, which includes setting
        releasability on all CRITs objects.)
        Raises UnreleasableEventError if the releasability on the
        relationships and the event do not share any common releasability
        sources.
        """

        from crits.emails.email import Email
        from crits.samples.sample import Sample
        from crits.indicators.indicator import Indicator

        from cybox.common import Time, ToolInformationList, ToolInformation
        from cybox.core import Observables
        from stix.common import StructuredText
        from stix.core import STIXPackage, STIXHeader
        from stix.common import InformationSource
        from stix.common.identity import Identity

        stix_indicators = []
        stix_observables = []
        final_objects = []

        # create a list of sources to send as part of the results.
        # list should be limited to the sources this user is allowed to use.
        # this list should be used along with the list of objects to set the
        # appropriate source's 'released' key to True for each object.
        final_sources = []
        user_source_list = user_sources(username)
        for f in self.releasability:
            if f.name in user_source_list:
                final_sources.append(f.name)
        final_sources = set(final_sources)

        # TODO: eventually we can use class_from_id instead of the if block
        #       but only once we support all CRITs types.
        for r in self.relationships:
            obj = None
            if r.rel_type == Email._meta['crits_type']:
                obj = Email.objects(id=r.object_id,
                                    source__name__in=user_source_list).first()
                if obj:
                    ind, releas = obj.to_cybox()
                    stix_observables.append(ind[0])
            elif r.rel_type == Sample._meta['crits_type']:
                obj = Sample.objects(id=r.object_id,
                                    source__name__in=user_source_list).first()
                if obj:
                    ind, releas = obj.to_cybox()
                    for i in ind:
                        stix_observables.append(i)
            elif r.rel_type == Indicator._meta['crits_type']:
                #NOTE: Currently this will raise an exception if there
                #   are multiple indicators with the same value.
                #   Should be fixed automatically once we transition
                #   indicators to be related based on ObjectId rather
                #   than value.
                obj = Indicator.objects(id=r.object_id,
                                    source__name__in=user_source_list).first()
                if obj:
                    ind, releas = obj.to_stix_indicator()
                    stix_indicators.append(ind)
            else:
                continue
            #Create a releasability list that is the intersection of
            #   each related item's releasability with the event's
            #   releasability. If the resulting set is empty, raise exception
            #TODO: Set releasability on all objects so that we actually
            #   get results here instead of always raising an exception.
            if obj:
                releas_sources = set([rel.name for rel in releas])
                final_sources = final_sources.intersection(releas_sources)
                #TODO: uncomment the following lines when objects have
                #   releasability set.
                #if not final_sources:
                #    raise UnreleasableEventError(r.value)

                # add to the final_objects list to send as part of the results
                final_objects.append(obj)

        tool_list = ToolInformationList()
        tool = ToolInformation("CRITs", "MITRE")
        tool.version = settings.CRITS_VERSION
        tool_list.append(tool)
        i_s = InformationSource(
                time=Time(produced_time= datetime.datetime.now()),
                identity = Identity(name=settings.COMPANY_NAME),
                tools = tool_list
        )
        description = StructuredText(value=self.description)
        header = STIXHeader(information_source=i_s,
                            description=description,
                            package_intent=self.event_type,
                            title=self.title)

        return (STIXPackage(indicators=stix_indicators,
                            observables=Observables(stix_observables),
                            stix_header=header,
                            id_=self.event_id),
                final_sources,
                final_objects)

    @classmethod
    def from_stix(cls, stix_package, source):
        """
        Converts a stix_package to a CRITs Event.

        :param stix_package: A stix package.
        :type stix_package: :class:`stix.core.STIXPackage`
        :param source: The source list for this STIX package.
        :type source: list
        :returns: None, :class:`crits.events.event.Event'
        """

        from stix.common import StructuredText
        from stix.core import STIXPackage, STIXHeader

        if isinstance(stix_package, STIXPackage):
            stix_header = stix_package.stix_header
            stix_id = stix_package.id_
            event = cls(source=source)
            event.title = "STIX Document %s" % stix_id
            event.event_type = "Collective Threat Intelligence"
            event.description = str(datetime.datetime.now())
            try:
                event.event_id = uuid.UUID(stix_id)
            except:
                if event.source[0].instances[0].reference:
                    event.source[0].instances[0].reference += ", STIX ID: %s" % stix_id
                else:
                    event.source[0].instances[0].reference = "STIX ID: %s" % stix_id
            if isinstance(stix_header, STIXHeader):
                if stix_header.title:
                    event.title = stix_header.title
                if stix_header.package_intent:
                    event.event_type = str(stix_header.package_intent)
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
