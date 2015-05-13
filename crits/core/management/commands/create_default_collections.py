import os

from django.conf import settings
from django.core.management.base import BaseCommand
from optparse import make_option

from create_indexes import create_indexes
from create_event_types import add_event_types
from create_locations import add_location_objects
from create_object_types import add_object_types
from create_relationship_types import add_relationship_types
from create_sectors import add_sector_objects
from setconfig import create_config_if_not_exist
from create_actors_content import add_actor_content
from create_default_dashboard import create_dashboard

from crits.core.user_role import UserRole
from crits.domains.domain import TLD
from crits.indicators.indicator import IndicatorAction
from crits.raw_data.raw_data import RawDataType

class Command(BaseCommand):
    """
    Script Class.
    """

    option_list = BaseCommand.option_list + (
        make_option('--drop',
                    '-d',
                    dest='drop',
                    action="store_true",
                    default=False,
                    help='Drop existing content before adding.'),
    )
    help = 'Creates default CRITs collections in MongoDB.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        drop = options.get('drop')
        if drop:
            print "Dropping enabled. Will drop content before adding!"
        else:
            print "Drop protection enabled. Will not drop existing content!"
        populate_user_roles(drop)
        populate_indicator_actions(drop)
        populate_raw_data_types(drop)
        # The following will always occur with every run of this script:
        #   - tlds are based off of a Mozilla TLD list so it should never
        #     contain  entries outside of the ones provided.
        #   - object types are based off of the CybOX standard (with very few
        #   exceptions) so we will always repopulate with the list above.
        #   - relationship types are based off of the CybOX standard so we will
        #   always populate with the list above.
        # If you wish to add your own custom relationship types or object types
        # (not recommended), then be sure to add them above so they will be
        # added back if this script were to be used again.
        populate_tlds(drop)
        add_relationship_types(drop)
        add_object_types(drop)
        add_event_types(drop)
        add_location_objects(drop)
        add_sector_objects(drop)
        add_actor_content(drop)
        create_dashboard(drop)
        create_config_if_not_exist()
        create_indexes()


def populate_user_roles(drop):
    """
    Populate default set of user roles into the system.

    :param drop: Drop the existing collection before trying to populate.
    :type: boolean
    """

    # define your user roles here
    # note: you MUST have Administrator, Read Only, and a third option
    # available!
    user_roles = ['Administrator', 'Analyst', 'Read Only']
    if drop:
        UserRole.drop_collection()
    if len(UserRole.objects()) < 1:
        for role in user_roles:
            ur = UserRole()
            ur.name = role
            ur.save()
        print "User Roles: added %s roles!" % len(user_roles)
    else:
        print "User Roles: existing documents detected. skipping!"

def populate_indicator_actions(drop):
    """
    Populate default set of Indicator Actions into the system.

    :param drop: Drop the existing collection before trying to populate.
    :type: boolean
    """

    # define your indicator actions here
    actions = ['Blocked Outbound At Firewall', 'Blocked Outbound At Desktop Firewall']
    if drop:
        IndicatorAction.drop_collection()
    if len(IndicatorAction.objects()) < 1:
        for action in actions:
            ia = IndicatorAction()
            ia.name = action
            ia.save()
        print "Indicator Actions: added %s actions!" % len(actions)
    else:
        print "Indicator Actions: existing documents detected. skipping!"

def populate_raw_data_types(drop):
    """
    Populate default set of raw data types into the system.

    :param drop: Drop the existing collection before trying to populate.
    :type: boolean
    """

    # define your raw data types here
    data_types = ['Text', 'JSON']
    if drop:
        RawDataType.drop_collection()
    if len(RawDataType.objects()) < 1:
        for data_type in data_types:
            dt = RawDataType()
            dt.name = data_type
            dt.save()
        print "Raw Data Types: added %s types!" % len(data_types)
    else:
        print "Raw Data Types: existing documents detected. skipping!"

def populate_tlds(drop):
    """
    Populate default set of TLDs into the system.

    :param drop: Drop the existing collection before trying to populate.
    :type: boolean
    """

    if not drop:
        print "Drop protection does not apply to effective TLDs"
    TLD.drop_collection()
    f = os.path.join(settings.SITE_ROOT, '..', 'extras', 'effective_tld_names.dat')
    count = 0
    for line in open(f, 'r').readlines():
        line = line.strip()
        if line and not line.startswith('//'):
            TLD.objects(tld=line).update_one(set__tld=line, upsert=True)
            count += 1
    print "Effective TLDs: added %s TLDs!" % count
