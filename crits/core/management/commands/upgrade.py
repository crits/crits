import sys

from django.core.management.base import BaseCommand
from django.conf import settings
from optparse import make_option

from crits.actors.actor import Actor
from crits.backdoors.backdoor import Backdoor
from crits.campaigns.campaign import Campaign
from crits.certificates.certificate import Certificate
from crits.config.config import CRITsConfig
from crits.domains.domain import Domain
from crits.emails.email import Email
from crits.events.event import Event
from crits.exploits.exploit import Exploit
from crits.indicators.indicator import Indicator
from crits.ips.ip import IP
from crits.pcaps.pcap import PCAP
from crits.raw_data.raw_data import RawData
from crits.signatures.signature import Signature
from crits.samples.sample import Sample
from crits.targets.target import Target

from prep import prep_database

class Command(BaseCommand):
    """
    Script Class.
    """

    option_list = BaseCommand.option_list + (
        make_option("-a", "--migrate_all", action="store_true", dest="mall",
                    default=False,
                    help="Migrate all collections."),
        make_option("-A", "--migrate_actors", action="store_true",
                    dest="actors",
                    default=False,
                    help="Migrate actors."),
        make_option("-b", "--migrate_backdoors", action="store_true",
                    dest="backdoors",
                    default=False,
                    help="Migrate backdoors."),
        make_option("-c", "--migrate_campaigns", action="store_true",
                    dest="campaigns",
                    default=False,
                    help="Migrate campaigns."),
        make_option("-C", "--migrate_certificates", action="store_true",
                    dest="certificates",
                    default=False,
                    help="Migrate certificates."),
        make_option("-D", "--migrate_domains", action="store_true",
                    dest="domains",
                    default=False,
                    help="Migrate domains."),
        make_option("-e", "--migrate_emails", action="store_true",
                    dest="emails",
                    default=False,
                    help="Migrate emails."),
        make_option("-E", "--migrate_events", action="store_true",
                    dest="events",
                    default=False,
                    help="Migrate events."),
        make_option("-i", "--migrate_indicators", action="store_true",
                    dest="indicators",
                    default=False,
                    help="Migrate indicators."),
        make_option("-I", "--migrate_ips", action="store_true",
                    dest="ips",
                    default=False,
                    help="Migrate ips."),
        make_option("-o", "--sort-ids", action="store_true", dest="sort_ids",
                    default=False,
                    help="Sort by ObjectId before migrating."),
        make_option("-P", "--migrate_pcaps", action="store_true",
                    dest="pcaps",
                    default=False,
                    help="Migrate pcaps."),
        make_option("-r", "--migrate_raw_data", action="store_true",
                    dest="raw_data",
                    default=False,
                    help="Migrate raw data."),
        make_option("-g", "--migrate_signatures", action="store_true",
                    dest="signatures",
                    default=False,
                    help="Migrate signatures."),
        make_option("-s", "--skip_prep", action="store_true", dest="skip",
                    default=False,
                    help="Skip prepping the database"),
        make_option("-S", "--migrate_samples", action="store_true",
                    dest="samples",
                    default=False,
                    help="Migrate samples."),
        make_option("-T", "--migrate_targets", action="store_true",
                    dest="targets",
                    default=False,
                    help="Migrate targets."),
        make_option("-x", "--migrate_exploits", action="store_true",
                    dest="exploits",
                    default=False,
                    help="Migrate exploits."),
    )
    help = 'Upgrades MongoDB to latest version using mass-migration.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        lv = settings.CRITS_VERSION
        mall = options.get('mall')
        actors = options.get('actors')
        campaigns = options.get('campaigns')
        certificates = options.get('certificates')
        domains = options.get('domains')
        emails = options.get('emails')
        events = options.get('events')
        exploits = options.get('exploits')
        indicators = options.get('indicators')
        ips = options.get('ips')
        pcaps = options.get('pcaps')
        raw_data = options.get('raw_data')
        samples = options.get('samples')
        signatures = options.get('signatures')
        targets = options.get('targets')

        if (not mall and
            not actors and
            not campaigns and
            not certificates and
            not domains and
            not emails and
            not events and
            not exploits and
            not indicators and
            not ips and
            not pcaps and
            not raw_data and
            not samples and
            not signatures and
            not targets):
            print "You must select something to upgrade. See '-h' for options."
            sys.exit(1)
        else:
            upgrade(lv, options)

def migrate_collection(class_obj, sort_ids):
    """
    Migrate a collection by opening each document. This will, by nature of the
    core functionality in `crits.core.crits_mongoengine` check the
    schema_version and migrate it if it is not the latest version.

    :param class_obj: The class to migrate documents for.
    :type class_obj: class that inherits from
                     :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param sort_ids: If we should sort by ids ascending.
    :type sort_ids: boolean
    """

    # find all documents that don't have the latest schema version
    # and migrate those.
    version = class_obj._meta['latest_schema_version']
    if sort_ids:
        docs = (
            class_obj.objects(schema_version__lt=version)
            .order_by('+id')
            .timeout(False)
        )
    else:
        docs = class_obj.objects(schema_version__lt=version).timeout(False)
    print "Migrating %ss...%d" % (class_obj._meta['crits_type'], len(docs))
    count = 0
    doc = None
    try:
        for doc in docs:
            print >> sys.stdout, "\r\t%d" % (count + 1),
            sys.stdout.flush()
            if 'migrated' in doc._meta and doc._meta['migrated']:
                count += 1
    except Exception, e:
        # Provide some basic info so admin can query their db and figure out
        # what bad data is blowing up the migration.
        print "\n\tMigrated: %d" % count
        print "\tError: %s" % e
        if doc:
            print "\tLast ID: %s" % doc.id
        sys.exit(1)
    print "\n\t%d %ss migrated!" % (count, class_obj._meta['crits_type'])

def upgrade(lv, options):
    """
    Perform the upgrade.

    :param lv: The CRITs version we are running.
    :type lv: str
    :param options: The options passed in for what to upgrade.
    :type options: dict
    """

    # eventually we will do something to check to see what the current version
    # of the CRITs DB is so we can upgrade through several versions at once.
    # this is important if prep scripts need to be run for certain upgrades
    # to work properly.
    mall = options.get('mall')
    actors = options.get('actors')
    backdoors = options.get('backdoors')
    campaigns = options.get('campaigns')
    certificates = options.get('certificates')
    domains = options.get('domains')
    emails = options.get('emails')
    events = options.get('events')
    exploits = options.get('exploits')
    indicators = options.get('indicators')
    ips = options.get('ips')
    pcaps = options.get('pcaps')
    raw_data = options.get('raw_data')
    samples = options.get('samples')
    signatures = options.get('signatures')
    targets = options.get('targets')
    skip = options.get('skip')
    sort_ids = options.get('sort_ids')

    # run prep migrations
    if not skip:
        prep_database()

    # run full migrations
    if mall or actors:
        migrate_collection(Actor, sort_ids)
    if mall or backdoors:
        migrate_collection(Backdoor, sort_ids)
    if mall or campaigns:
        migrate_collection(Campaign, sort_ids)
    if mall or certificates:
        migrate_collection(Certificate, sort_ids)
    if mall or domains:
        migrate_collection(Domain, sort_ids)
    if mall or emails:
        migrate_collection(Email, sort_ids)
    if mall or events:
        migrate_collection(Event, sort_ids)
    if mall or indicators:
        migrate_collection(Indicator, sort_ids)
    if mall or ips:
        migrate_collection(IP, sort_ids)
    if mall or pcaps:
        migrate_collection(PCAP, sort_ids)
    if mall or raw_data:
        migrate_collection(RawData, sort_ids)
    if mall or samples:
        migrate_collection(Sample, sort_ids)
    if mall or signatures:
        migrate_collection(Signature, sort_ids)
    if mall or targets:
        migrate_collection(Target, sort_ids)
    if mall or exploits:
        migrate_collection(Exploit, sort_ids)

    # Always bump the version to the latest in settings.py
    config = CRITsConfig.objects()
    if len(config) > 1:
        print "You have more than one config object. This is really bad."
    else:
        config = config[0]
        config.crits_version = settings.CRITS_VERSION
        config.save()
