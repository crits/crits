import os

from django.conf import settings
from django.core.management.base import BaseCommand
from optparse import make_option

from create_indexes import create_indexes
from create_locations import add_location_objects
from setconfig import create_config_if_not_exist
from create_default_dashboard import create_dashboard

from crits.core.crits_mongoengine import Action
from crits.core.user_role import UserRole
from crits.domains.domain import TLD
from crits.raw_data.raw_data import RawDataType
from crits.signatures.signature import SignatureType


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
        populate_actions(drop)
        populate_raw_data_types(drop)
        populate_signature_types(drop)
        # The following will always occur with every run of this script:
        #   - tlds are based off of a Mozilla TLD list so it should never
        #     contain  entries outside of the ones provided.
        populate_tlds(drop)
        add_location_objects(drop)
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

def populate_actions(drop):
    """
    Populate default set of Actions into the system.

    :param drop: Drop the existing collection before trying to populate.
    :type: boolean
    """

    # define your Actions here
    actions = ['Blocked Outbound At Firewall', 'Blocked Outbound At Desktop Firewall']
    if drop:
        Action.drop_collection()
    if len(Action.objects()) < 1:
        for action in actions:
            ia = Action()
            ia.name = action
            ia.save()
        print "Actions: added %s actions!" % len(actions)
    else:
        print "Actions: existing documents detected. skipping!"


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


def populate_signature_types(drop):
    """
    Populate default set of signature types into the system.

    :param drop: Drop the existing collection before trying to populate.
    :type: boolean
    """

    # define your signature types here
    data_types = ['Bro', 'Snort', 'Yara']
    if drop:
        SignatureType.drop_collection()
    if len(SignatureType.objects()) < 1:
        for data_type in data_types:
            dt = SignatureType()
            dt.name = data_type
            dt.save()
        print "Signature Types: added %s types!" % len(data_types)
    else:
        print "Signature Types: existing documents detected. skipping!"


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
