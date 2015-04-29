import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from crits.locations.location import Location

class Command(BaseCommand):
    """
    Script Class.
    """

    help = 'Creates location objects in MongoDB.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        add_location_objects(True)

def add_location_objects(drop=False):
    """
    Add location objects to the system.

    :param drop: Drop collection before adding.
    :type drop: boolean
    """

    f = os.path.join(settings.SITE_ROOT,
                     '..',
                     'extras',
                     'countries.json')
    locations = open(f, 'r')
    cdata = locations.read()
    data = json.loads(cdata)

    if not drop:
        print "Drop protection does not apply to location objects"
    Location.drop_collection()

    count = 0
    for location in data:
        l = Location()
        l.name = location['name']['official']
        l.calling_code = get_value(location['callingCode'])
        l.cca2 = location['cca2']
        l.cca3 = location['cca3']
        l.ccn3 = location['ccn3']
        l.cioc = location['cioc']
        l.region = location['region']
        l.sub_region = location['subregion']
        l.latitude = get_lat(location['latlng'])
        l.longitude = get_long(location['latlng'])
        l.save()
        count += 1
    print "Added %s Location Objects." % count

def get_value(value):
    v = None
    if isinstance(value, list):
        if len(value) < 1:
            return v
        else:
            v = value[0]
    else:
        v = value
    return v

def get_lat(value):
    if isinstance(value, list):
        if len(value) < 2:
            return None
        else:
            return value[0]

def get_long(value):
    if isinstance(value, list):
        if len(value) < 2:
            return None
        else:
            return value[1]
