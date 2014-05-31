import datetime
import logging

from bson.objectid import ObjectId
from django.conf import settings
from django.core.management.base import BaseCommand
from dateutil.parser import parse

from crits.core.audit import AuditLog
from crits.core.mongo_tools import mongo_find, mongo_find_one, mongo_update
from crits.core.source_access import SourceAccess
from crits.core.user_role import UserRole
from crits.indicators.indicator import IndicatorAction
from crits.samples.backdoor import Backdoor
from crits.samples.exploit import Exploit
from crits.samples.yarahit import YaraHit
from crits.targets.division import Division

from setconfig import create_config_if_not_exist

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

    print "Adjusting Audit Log Dates..."
    col = settings.COL_AUDIT_LOG
    schema_version = AuditLog._meta['latest_schema_version']
    entries = mongo_find(col, {})
    total = 0
    for entry in entries:
        changes = {}
        changes['schema_version'] = schema_version
        if 'date' in entry:
            if not isinstance(entry['date'], datetime.datetime):
                changes['date'] = parse(entry['date'], fuzzy=True)
                total += 1
            else:
                changes['date'] = entry['date']
        mongo_update(col,
                    {'_id': ObjectId(entry['_id'])},
                    {'$set': changes})
    print "Fixed %s audit log entries!\n" % total

def prep_backdoors():
    """
    Migrate backdoors.
    """

    # fix backdoors not having schema_versions
    sv = Backdoor._meta['latest_schema_version']
    mongo_update(settings.COL_BACKDOOR_DETAILS,
                 {'schema_version': {'$exists': 0}},
                 {'$set': {'schema_version': sv}})
    print "Fixed backdoors without a schema!\n"

def prep_campaigns():
    """
    Migrate campaigns.
    """

    pass

def prep_comments():
    """
    Migrate comments.
    """

    print "Adjusting comment url_keys..."
    col = settings.COL_COMMENTS
    query = {'url_key': {'$type': 7}}
    comments = mongo_find(col, query)
    total = 0
    for comment in comments:
        _id = comment['_id']
        url_key = str(comment['url_key'])
        mongo_update(col,
                     {'_id': ObjectId(_id)},
                     {'$set': {'url_key': url_key}})
        total += 1
    print "Fixed %s comments, correcting ObjectId url_key!\n" % total

    query = {'obj_type': "Campaign",  "url_key": {'$exists': 0} }
    comments = mongo_find(col, query)
    total = 0
    for comment in comments:
        _id = comment['_id']
        obj = mongo_find_one(settings.COL_CAMPAIGNS, {"_id": comment['obj_id']})
        if obj:
            url_key = obj['name']
            mongo_update(col,
                         {'_id': ObjectId(_id)},
                         {'$set': {'url_key': url_key}})
            total += 1
    print "Fixed %s comments, correcting url_key based on obj_id!\n" % total

def prep_divisions():
    """
    Migrate divisions.
    """

    # fix divisions not having schema_versions
    sv = Division._meta['latest_schema_version']
    mongo_update(settings.COL_DIVISION_DATA,
                 {'schema_version': {'$exists': 0}},
                 {'$set': {'schema_version': sv}})
    print "Fixed divisions without a schema!\n"

def prep_events():
    """
    Migrate events.
    """

    pass

def prep_exploits():
    """
    Migrate exploits.
    """

    # fix exploits not having schema_versions
    sv = Exploit._meta['latest_schema_version']
    mongo_update(settings.COL_EXPLOIT_DETAILS,
                 {'schema_version': {'$exists': 0}},
                 {'$set': {'schema_version': sv}})
    print "Fixed exploits without a schema!\n"

def prep_indicator_actions():
    """
    Migrate indicator actions.
    """

    # fix indicator actions not having schema_versions
    sv = IndicatorAction._meta['latest_schema_version']
    mongo_update(settings.COL_IDB_ACTIONS,
                 {'schema_version': {'$exists': 0}},
                 {'$set': {'schema_version': sv}})
    print "Fixed Indicator Actions without a schema!\n"

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

    # fix source_access not having schema_versions
    sv = SourceAccess._meta['latest_schema_version']
    mongo_update(settings.COL_SOURCE_ACCESS,
                 {'schema_version': {'$exists': 0}},
                 {'$set': {'schema_version': sv}})
    print "Fixed sources without a schema!\n"

def prep_user_roles():
    """
    Migrate user roles.
    """

    # fix user_roles not having schema_versions
    sv = UserRole._meta['latest_schema_version']
    mongo_update(settings.COL_USER_ROLES,
                 {'schema_version': {'$exists': 0}},
                 {'$set': {'schema_version': sv}})
    print "Fixed user roles without a schema!\n"

def prep_yarahits():
    """
    Migrate yara hits.
    """

    # fix yarahits not having schema_versions
    sv = YaraHit._meta['latest_schema_version']
    mongo_update(settings.COL_YARAHITS,
                 {'schema_version': {'$exists': 0}},
                 {'$set': {'schema_version': sv}})
    print "Fixed yara hits without a schema!\n"

def prep_database():
    """
    Migrate the appropriate collections.
    """

    create_config_if_not_exist()
    prep_audit_log()
    prep_comments()
    prep_backdoors()
    prep_divisions()
    prep_exploits()
    prep_indicator_actions()
    prep_sources()
    prep_user_roles()
    prep_yarahits()
