from django.core.management.base import BaseCommand

from crits.events.event import EventType

class Command(BaseCommand):
    """
    Script Class.
    """

    help = 'Creates Event Types in MongoDB.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        add_event_types(True)

def add_event_types(drop=False):
    """
    Add Event Types to the system.

    :param drop: Drop the contents of the collection before adding.
    :type drop: boolean
    """

    types = [
        'Collective Threat Intelligence',
        'Threat Report',
        'Indicators',
        'Indicators - Phishing',
        'Indicators - Watchlist',
        'Indicators - Malware Artifacts',
        'Indicators - Network Activity',
        'Indicators - Endpoint Characteristics',
        'Campaign Characterization',
        'Threat Actor Characterization',
        'Exploit Characterization',
        'Attack Pattern Characterization',
        'Malware Characterization',
        'TTP - Infrastructure',
        'TTP - Tools',
        'Courses of Action',
        'Incident',
        'Observations',
        'Observations - Email',
        'Malware Samples',
    ]
    if not drop:
        print "Drop protection does not apply to event types"
    EventType.drop_collection()
    count = 0
    for t in types:
        et = EventType()
        et.name = t
        et.active = "on"
        et.save()
        count += 1
    print "Added %s Event Types." % count
