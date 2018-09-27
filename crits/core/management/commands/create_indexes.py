import pymongo
from django.core.management.base import BaseCommand

from django.conf import settings


from crits.core.mongo_tools import mongo_connector

class Command(BaseCommand):
    """
    Script Class.
    """

    def add_arguments(self, parser):

        parser.add_argument('--remove-indexes',
                        '-r',
                        action='store_true',
                        dest='remove',
                        default=False,
                        help='Remove all indexes. Does NOT create.')
    
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

    coll_list = [settings.COL_ANALYSIS_RESULTS,
                 settings.COL_BACKDOORS,
                 settings.COL_BUCKET_LISTS,
                 settings.COL_CAMPAIGNS,
                 settings.COL_COMMENTS,
                 settings.COL_DOMAINS,
                 settings.COL_EMAIL,
                 settings.COL_EVENTS,
                 settings.COL_EXPLOITS,
                 settings.COL_INDICATORS,
                 settings.COL_IPS,
                 settings.COL_OBJECTS,
                 settings.COL_NOTIFICATIONS,
                 '%s.files' % settings.COL_OBJECTS,
                 '%s.chunks' % settings.COL_OBJECTS,
                 settings.COL_PCAPS,
                 '%s.files' % settings.COL_PCAPS,
                 '%s.chunks' % settings.COL_PCAPS,
                 settings.COL_RAW_DATA,
                 settings.COL_SAMPLES,
                 '%s.files' % settings.COL_SAMPLES,
                 '%s.chunks' % settings.COL_SAMPLES,
                 settings.COL_SCREENSHOTS,
                 settings.COL_SIGNATURES,
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
    analysis_results.create_index("service_name", background=True)
    analysis_results.create_index("object_type", background=True)
    analysis_results.create_index("object_id", background=True)
    analysis_results.create_index("start_date", background=True)
    analysis_results.create_index("finish_date", background=True)
    analysis_results.create_index("version", background=True)
    analysis_results.create_index("analysis_id", background=True)

    bucket_lists = mongo_connector(settings.COL_BUCKET_LISTS)
    bucket_lists.create_index("name", background=True)

    backdoors = mongo_connector(settings.COL_BACKDOORS)
    backdoors.create_index("name", background=True)

    campaigns = mongo_connector(settings.COL_CAMPAIGNS)
    campaigns.create_index("objects.value", background=True)
    campaigns.create_index("relationships.value", background=True)
    campaigns.create_index("bucket_list", background=True)

    comments = mongo_connector(settings.COL_COMMENTS)
    comments.create_index("obj_id", background=True)
    comments.create_index("users", background=True)
    comments.create_index("tags", background=True)
    comments.create_index("status", background=True)

    domains = mongo_connector(settings.COL_DOMAINS)
    domains.create_index("domain", background=True)
    domains.create_index("objects.value", background=True)
    domains.create_index("relationships.value", background=True)
    domains.create_index("campaign.name", background=True)
    domains.create_index("bucket_list", background=True)

    emails = mongo_connector(settings.COL_EMAIL)
    emails.create_index("objects.value", background=True)
    emails.create_index("relationships.value", background=True)
    emails.create_index("campaign.name", background=True)
    emails.create_index("bucket_list", background=True)
    emails.create_index("favorite", background=True)
    emails.create_index("from", background=True)
    emails.create_index("source.name", background=True)
    emails.create_index("status", background=True)
    emails.create_index("subject", background=True)
    emails.create_index("isodate", background=True)

    events = mongo_connector(settings.COL_EVENTS)
    events.create_index("objects.value", background=True)
    events.create_index("title", background=True)
    events.create_index("relationships.value", background=True)
    events.create_index("campaign.name", background=True)
    events.create_index("source.name", background=True)
    events.create_index([("created", pymongo.DESCENDING)], background=True)
    events.create_index("status", background=True)
    events.create_index("favorite", background=True)
    events.create_index("event_type", background=True)
    events.create_index("bucket_list", background=True)

    exploits = mongo_connector(settings.COL_EXPLOITS)
    exploits.create_index("name", background=True)

    indicators = mongo_connector(settings.COL_INDICATORS)
    indicators.create_index("value", background=True)
    indicators.create_index("lower", background=True)
    indicators.create_index("objects.value", background=True)
    indicators.create_index("relationships.value", background=True)
    indicators.create_index("campaign.name", background=True)
    indicators.create_index([("created", pymongo.DESCENDING)], background=True)
    indicators.create_index([("modified", pymongo.DESCENDING)], background=True)
    indicators.create_index("type", background=True)
    indicators.create_index("status", background=True)
    indicators.create_index("source.name", background=True)
    indicators.create_index("bucket_list", background=True)

    ips = mongo_connector(settings.COL_IPS)
    ips.create_index("ip", background=True)
    ips.create_index("objects.value", background=True)
    ips.create_index("relationships.value", background=True)
    ips.create_index("campaign.name", background=True)
    ips.create_index([("created", pymongo.DESCENDING)], background=True)
    ips.create_index([("modified", pymongo.DESCENDING)], background=True)
    ips.create_index("source.name", background=True)
    ips.create_index("status", background=True)
    ips.create_index("type", background=True)
    ips.create_index("favorite", background=True)
    ips.create_index("bucket_list", background=True)

    if settings.FILE_DB == settings.GRIDFS:
        objects_files = mongo_connector('%s.files' % settings.COL_OBJECTS)
        objects_files.create_index("md5", background=True)

        objects_chunks = mongo_connector('%s.chunks' % settings.COL_OBJECTS)
        objects_chunks.create_index([("files_id",pymongo.ASCENDING),
                                ("n", pymongo.ASCENDING)],
                               unique=True)

    notifications = mongo_connector(settings.COL_NOTIFICATIONS)
    notifications.create_index("obj_id", background=True)
    # auto-expire notifications after 30 days
    notifications.create_index("date", background=True,
                               expireAfterSeconds=2592000)
    notifications.create_index("users", background=True)

    pcaps = mongo_connector(settings.COL_PCAPS)
    pcaps.create_index("md5", background=True)
    pcaps.create_index("objects.value", background=True)
    pcaps.create_index("relationships.value", background=True)
    pcaps.create_index("campaign.name", background=True)
    pcaps.create_index("filename", background=True)
    pcaps.create_index("description", background=True)
    pcaps.create_index("length", background=True)
    pcaps.create_index([("modified", pymongo.DESCENDING)], background=True)
    pcaps.create_index("source.name", background=True)
    pcaps.create_index("status", background=True)
    pcaps.create_index("favorite", background=True)
    pcaps.create_index("bucket_list", background=True)

    if settings.FILE_DB == settings.GRIDFS:
        pcaps_files = mongo_connector('%s.files' % settings.COL_PCAPS)
        pcaps_files.create_index("md5", background=True)

        pcaps_chunks = mongo_connector('%s.chunks' % settings.COL_PCAPS)
        pcaps_chunks.create_index([("files_id", pymongo.ASCENDING),
                                ("n", pymongo.ASCENDING)],
                               unique=True)

    raw_data = mongo_connector(settings.COL_RAW_DATA)
    raw_data.create_index("link_id", background=True)
    raw_data.create_index("md5", background=True)
    raw_data.create_index("title", background=True)
    raw_data.create_index("data_type", background=True)
    raw_data.create_index("version", background=True)
    raw_data.create_index([("modified", pymongo.DESCENDING)], background=True)
    raw_data.create_index("source.name", background=True)
    raw_data.create_index("objects.value", background=True)
    raw_data.create_index("relationships.value", background=True)
    raw_data.create_index("campaign.name", background=True)
    raw_data.create_index("status", background=True)
    raw_data.create_index("favorite", background=True)
    raw_data.create_index("bucket_list", background=True)

    samples = mongo_connector(settings.COL_SAMPLES)
    samples.create_index("source.name", background=True)
    samples.create_index("md5", background=True)
    samples.create_index("sha1", background=True)
    samples.create_index("sha256", background=True)
    samples.create_index("ssdeep", background=True)
    samples.create_index("impfuzzy", background=True)
    samples.create_index("mimetype", background=True)
    samples.create_index("filetype", background=True)
    samples.create_index("size", background=True)
    samples.create_index("filename", background=True)
    samples.create_index("objects.value", background=True)
    samples.create_index("relationships.value", background=True)
    samples.create_index("campaign.name", background=True)
    samples.create_index("analysis.results.result", background=True)
    samples.create_index("analysis.results.md5", background=True)
    samples.create_index("bucket_list", background=True)
    samples.create_index([("created", pymongo.DESCENDING)], background=True)
    samples.create_index([("modified", pymongo.DESCENDING)], background=True)
    samples.create_index("favorite", background=True)
    samples.create_index("status", background=True)

    if settings.FILE_DB == settings.GRIDFS:
        samples_files = mongo_connector('%s.files' % settings.COL_SAMPLES)
        samples_files.create_index("md5", background=True)

        samples_chunks = mongo_connector('%s.chunks' % settings.COL_SAMPLES)
        samples_chunks.create_index([("files_id", pymongo.ASCENDING),
                                  ("n", pymongo.ASCENDING)],
                                 unique=True)

    screenshots = mongo_connector(settings.COL_SCREENSHOTS)
    screenshots.create_index("tags", background=True)

    signature = mongo_connector(settings.COL_SIGNATURES)
    signature.create_index("link_id", background=True)
    signature.create_index("md5", background=True)
    signature.create_index("title", background=True)
    signature.create_index("data_type", background=True)
    signature.create_index("data_type_min_version", background=True)
    signature.create_index("data_type_max_version", background=True)
    signature.create_index("data_type_dependency", background=True)
    signature.create_index("version", background=True)
    signature.create_index([("modified", pymongo.DESCENDING)], background=True)
    signature.create_index("source.name", background=True)
    signature.create_index("objects.value", background=True)
    signature.create_index("relationships.value", background=True)
    signature.create_index("campaign.name", background=True)
    signature.create_index("status", background=True)
    signature.create_index("favorite", background=True)
    signature.create_index("bucket_list", background=True)

    targets = mongo_connector(settings.COL_TARGETS)
    targets.create_index("objects.value", background=True)
    targets.create_index("relationships.value", background=True)
    targets.create_index("email_address", background=True)
    targets.create_index("firstname", background=True)
    targets.create_index("lastname", background=True)
    targets.create_index("email_count", background=True)
    targets.create_index("campaign.name", background=True)
    targets.create_index("department", background=True)
    targets.create_index("division", background=True)
    targets.create_index("status", background=True)
    targets.create_index("favorite", background=True)
    targets.create_index("bucket_list", background=True)
