import pymongo
from django.core.management.base import BaseCommand

from django.conf import settings
from optparse import make_option

from crits.core.mongo_tools import mongo_connector

class Command(BaseCommand):
    """
    Script Class.
    """

    option_list = BaseCommand.option_list + (
        make_option('--remove-indexes',
                    '-r',
                    action='store_true',
                    dest='remove',
                    default=False,
                    help='Remove all indexes. Does NOT create.'),
    )
    help = 'Creates indexes for MongoDB.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        remove = options.get('remove')
        if remove:
            remove_indexes()
        else:
            create_indexes()

def remove_indexes():
    """
    Removes all indexes from all collections.
    """

    coll_list = [settings.COL_BACKDOORS,
                 settings.COL_BUCKET_LISTS,
                 settings.COL_CAMPAIGNS,
                 settings.COL_COMMENTS,
                 settings.COL_DOMAINS,
                 settings.COL_EMAIL,
                 settings.COL_EVENTS,
                 settings.COL_EXPLOITS,
                 settings.COL_INDICATORS,
                 settings.COL_IPS,
                 settings.COL_NOTIFICATIONS,
                 '%s.files' % settings.COL_OBJECTS,
                 '%s.chunks' % settings.COL_OBJECTS,
                 settings.COL_PCAPS,
                 '%s.files' % settings.COL_PCAPS,
                 '%s.chunks' % settings.COL_PCAPS,
                 settings.COL_SAMPLES,
                 '%s.files' % settings.COL_SAMPLES,
                 '%s.chunks' % settings.COL_SAMPLES,
                 settings.COL_TARGETS,
                 ]

    for coll in coll_list:
        print "Removing index for: %s" % coll
        c = mongo_connector(coll)
        c.drop_indexes()

def create_indexes():
    """
    Creates the default set of indexes for the system. Depending on your use
    cases, as well as quantity of data, admins may wish to tweak these indexes
    to best fit their requirements.
    """

    print "Creating indexes (duplicates will be ignored automatically)"

    analysis_results = mongo_connector(settings.COL_ANALYSIS_RESULTS)
    analysis_results.ensure_index("service_name", background=True)
    analysis_results.ensure_index("object_type", background=True)
    analysis_results.ensure_index("object_id", background=True)

    bucket_lists = mongo_connector(settings.COL_BUCKET_LISTS)
    bucket_lists.ensure_index("name", background=True)

    backdoors = mongo_connector(settings.COL_BACKDOORS)
    backdoors.ensure_index("name", background=True)

    campaigns = mongo_connector(settings.COL_CAMPAIGNS)
    campaigns.ensure_index("objects.value", background=True)
    campaigns.ensure_index("relationships.value", background=True)
    campaigns.ensure_index("bucket_list", background=True)

    comments = mongo_connector(settings.COL_COMMENTS)
    comments.ensure_index("obj_id", background=True)
    comments.ensure_index("users", background=True)
    comments.ensure_index("tags", background=True)
    comments.ensure_index("status", background=True)

    domains = mongo_connector(settings.COL_DOMAINS)
    domains.ensure_index("domain", background=True)
    domains.ensure_index("objects.value", background=True)
    domains.ensure_index("relationships.value", background=True)
    domains.ensure_index("campaign.name", background=True)
    domains.ensure_index("bucket_list", background=True)

    emails = mongo_connector(settings.COL_EMAIL)
    emails.ensure_index("objects.value", background=True)
    emails.ensure_index("relationships.value", background=True)
    emails.ensure_index("campaign.name", background=True)
    emails.ensure_index("bucket_list", background=True)

    events = mongo_connector(settings.COL_EVENTS)
    events.ensure_index("objects.value", background=True)
    events.ensure_index("relationships.value", background=True)
    events.ensure_index("campaign.name", background=True)
    events.ensure_index("bucket_list", background=True)

    exploits = mongo_connector(settings.COL_EXPLOITS)
    exploits.ensure_index("name", background=True)

    indicators = mongo_connector(settings.COL_INDICATORS)
    indicators.ensure_index("value", background=True)
    indicators.ensure_index("objects.value", background=True)
    indicators.ensure_index("relationships.value", background=True)
    indicators.ensure_index("campaign.name", background=True)
    indicators.ensure_index("bucket_list", background=True)

    ips = mongo_connector(settings.COL_IPS)
    ips.ensure_index("ip", background=True)
    ips.ensure_index("objects.value", background=True)
    ips.ensure_index("relationships.value", background=True)
    ips.ensure_index("campaign.name", background=True)
    ips.ensure_index("bucket_list", background=True)

    if settings.FILE_DB == settings.GRIDFS:
        objects_files = mongo_connector('%s.files' % settings.COL_OBJECTS)
        objects_files.ensure_index("md5", background=True)

        objects_chunks = mongo_connector('%s.chunks' % settings.COL_OBJECTS)
        objects_chunks.ensure_index([("files_id",pymongo.ASCENDING),
                                ("n", pymongo.ASCENDING)],
                               unique=True)

    notifications = mongo_connector(settings.COL_NOTIFICATIONS)
    notifications.ensure_index("obj_id", background=True)
    # auto-expire notifications after 30 days
    notifications.ensure_index("date", background=True,
                               expireAfterSeconds=2592000)
    notifications.ensure_index("users", background=True)

    pcaps = mongo_connector(settings.COL_PCAPS)
    pcaps.ensure_index("md5", background=True)
    pcaps.ensure_index("objects.value", background=True)
    pcaps.ensure_index("relationships.value", background=True)
    pcaps.ensure_index("campaign.name", background=True)
    pcaps.ensure_index("bucket_list", background=True)

    if settings.FILE_DB == settings.GRIDFS:
        pcaps_files = mongo_connector('%s.files' % settings.COL_PCAPS)
        pcaps_files.ensure_index("md5", background=True)

        pcaps_chunks = mongo_connector('%s.chunks' % settings.COL_PCAPS)
        pcaps_chunks.ensure_index([("files_id", pymongo.ASCENDING),
                                ("n", pymongo.ASCENDING)],
                               unique=True)

    raw_data = mongo_connector(settings.COL_RAW_DATA)
    raw_data.ensure_index("link_id", background=True)
    raw_data.ensure_index("md5", background=True)
    raw_data.ensure_index("objects.value", background=True)
    raw_data.ensure_index("relationships.value", background=True)
    raw_data.ensure_index("campaign.name", background=True)
    raw_data.ensure_index("bucket_list", background=True)

    samples = mongo_connector(settings.COL_SAMPLES)
    samples.ensure_index("source.name", background=True)
    samples.ensure_index("md5", background=True)
    samples.ensure_index("sha1", background=True)
    samples.ensure_index("sha256", background=True)
    samples.ensure_index("ssdeep", background=True)
    samples.ensure_index("mimetype", background=True)
    samples.ensure_index("filetype", background=True)
    samples.ensure_index("size", background=True)
    samples.ensure_index("filename", background=True)
    samples.ensure_index("objects.value", background=True)
    samples.ensure_index("relationships.value", background=True)
    samples.ensure_index("campaign.name", background=True)
    samples.ensure_index("analysis.results.result", background=True)
    samples.ensure_index("analysis.results.md5", background=True)
    samples.ensure_index("bucket_list", background=True)

    if settings.FILE_DB == settings.GRIDFS:
        samples_files = mongo_connector('%s.files' % settings.COL_SAMPLES)
        samples_files.ensure_index("md5", background=True)

        samples_chunks = mongo_connector('%s.chunks' % settings.COL_SAMPLES)
        samples_chunks.ensure_index([("files_id", pymongo.ASCENDING),
                                  ("n", pymongo.ASCENDING)],
                                 unique=True)

    screenshots = mongo_connector(settings.COL_SCREENSHOTS)
    screenshots.ensure_index("tags", background=True)

    targets = mongo_connector(settings.COL_TARGETS)
    targets.ensure_index("objects.value", background=True)
    targets.ensure_index("relationships.value", background=True)
    targets.ensure_index("campaign.name", background=True)
    targets.ensure_index("bucket_list", background=True)
