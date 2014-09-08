from django.core.management.base import BaseCommand
from stix.common import vocabs

from crits.actors.actor import ActorThreatType, ActorMotivation
from crits.actors.actor import ActorSophistication, ActorIntendedEffect


class Command(BaseCommand):
    """
    Script Class.
    """

    help = 'Creates Actor content from STIX in MongoDB.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        add_actor_content(True)

def add_actor_content(drop=False):
    """
    Add Actor content to the system. This is content based off of STIX and does
    not include Actor Identifiers which are not based on STIX.

    :param drop: Drop the collection before adding.
    :type drop: boolean
    """

    if not drop:
        print "Drop protection does not apply to actor content."

    ActorThreatType.drop_collection()
    ActorMotivation.drop_collection()
    ActorSophistication.drop_collection()
    ActorIntendedEffect.drop_collection()

    count = 0
    for t in vocabs.ThreatActorType._ALLOWED_VALUES:
        x = ActorThreatType(name = t)
        x.save()
        count += 1
    print "Added %s Threat Actor Types." % count
    count = 0
    for t in vocabs.Motivation._ALLOWED_VALUES:
        x = ActorMotivation(name = t)
        x.save()
        count += 1
    print "Added %s Actor Motivations." % count
    count = 0
    for t in vocabs.ThreatActorSophistication._ALLOWED_VALUES:
        x = ActorSophistication(name = t)
        x.save()
        count += 1
    print "Added %s Actor Sophistications." % count
    count = 0
    for t in vocabs.IntendedEffect._ALLOWED_VALUES:
        x = ActorIntendedEffect(name = t)
        x.save()
        count += 1
    print "Added %s Actor Intended Effects." % count
