import logging
import pymongo

from django.conf import settings
from django.core.management.base import BaseCommand

from crits.config.config import CRITsConfig
from crits.core.mongo_tools import mongo_update, mongo_remove, mongo_connector

from create_sectors import add_sector_objects



logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Script Class.
    """

    help = 'Preps MongoDB for upgrade.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        prep_database()

def prep_audit_log():
    """
    Migrate the audit log.
    """

    pass

def prep_backdoors():
    """
    Migrate backdoors.
    """

    pass

def prep_campaigns():
    """
    Migrate campaigns.
    """

    pass

def prep_comments():
    """
    Migrate comments.
    """

    pass

def prep_divisions():
    """
    Migrate divisions.
    """

    pass

def prep_events():
    """
    Migrate events.
    """

    pass

def prep_exploits():
    """
    Migrate exploits.
    """

    pass

def prep_indicator_actions():
    """
    Migrate indicator actions.
    """

    pass

def prep_indicators():
    """
    Migrate indicators.
    """

    pass

def prep_pcaps():
    """
    Migrate pcaps.
    """

    pass

def prep_targets():
    """
    Migrate targets.
    """

    pass

def prep_objects():
    """
    Migrate objects.
    """

    pass

def prep_relationships():
    """
    Migrate relationships.
    """

    pass

def prep_sources():
    """
    Migrate sources.
    """

    pass

def prep_user_roles():
    """
    Migrate user roles.
    """

    pass

def prep_yarahits():
    """
    Migrate yara hits.
    """

    pass

def prep_notifications():
    """
    Update notifications.
    """

    a1 = {"$unset": {"notifications": 1}}
    a2 = {"$unset": {"unsupported_attrs.notifications": 1}}
    mongo_update(settings.COL_USERS, {}, a1)
    mongo_update(settings.COL_USERS, {}, a2)
    query = {"type": "notification"}
    mongo_remove(settings.COL_COMMENTS, query)

def prep_sectors():

    add_sector_objects()

def prep_indexes():
    """
    Update indexing.
    """

    notifications = mongo_connector(settings.COL_NOTIFICATIONS)
    # auto-expire notifications after 30 days
    notifications.ensure_index("obj_id", background=True,
                               expireAfterSeconds=2592000)
    notifications.ensure_index("users", background=True)
    print "Notification indexes created."
    screenshots = mongo_connector(settings.COL_SCREENSHOTS)
    screenshots.ensure_index("tags", background=True)
    print "Screenshot indexes created."

    # check for old invalid chunk indexes and fix
    for col in ("%s.chunks" % settings.COL_OBJECTS,
                "%s.chunks" % settings.COL_PCAPS,
                "%s.chunks" % settings.COL_SAMPLES):
        c = mongo_connector(col)
        d = c.index_information()
        if d.get('files_id_1_n_1', False):
            b = d['files_id_1_n_1'].get('background', None)
            # background could be set to False or True in the DB
            if b is not None:
                c.drop_index("files_id_1_n_1")
                c.ensure_index([("files_id", pymongo.ASCENDING),
                                ("n", pymongo.ASCENDING)],
                               unique=True)
                print "Found bad index for %s. Fixed it." % col

def update_database_version():

    c = CRITsConfig.objects().first()
    c.crits_version = "3.1.0"
    c.save()

def prep_database():
    """
    Migrate the appropriate collections.
    """

    prep_notifications()
    prep_sectors()
    prep_indexes()
    update_database_version()
    return
