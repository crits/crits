from django.core.management.base import BaseCommand

from crits.core.sector import SectorObject

class Command(BaseCommand):
    """
    Script Class.
    """

    help = 'Creates sector objects in MongoDB.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        add_sector_objects(True)

def add_sector_objects(drop=False):
    """
    Add sector objects to the system.

    :param drop: Drop collection before adding.
    :type drop: boolean
    """

    # list comes from http://www.dhs.gov/critical-infrastructure-sectors
    sector_objects = [
        "Chemical",
        "Commercial Facilities",
        "Communications",
        "Critical Manufacturing",
        "Dams",
        "Defense Industrial Base",
        "Emergency Services",
        "Energy",
        "Financial Services",
        "Food and Agriculture",
        "Government Facilities",
        "Healthcare and Public Health",
        "Information Technology",
        "Nuclear Reactors Materials and Waste",
        "Transportation Systems",
        "Water and Wastewater Systems"
    ]
    if not drop:
        print "Drop protection does not apply to sector objects"
    SectorObject.drop_collection()
    count = 0
    for s in sector_objects:
        so = SectorObject()
        so.active = 'on'
        so.name = s
        so.save()
        count += 1
    print "Added %s Sector Objects." % count
