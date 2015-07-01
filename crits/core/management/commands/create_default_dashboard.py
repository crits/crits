from django.core.management.base import BaseCommand
from optparse import make_option

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
    help = 'Creates the default dashboard.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """
        drop = options.get('drop')
        if drop:
            print "Dropping enabled"
        else:
            print "Dropping protection enabled"
        create_dashboard(drop)

def create_dashboard(drop=False):
    from crits.dashboards.dashboard import SavedSearch, Dashboard
    if drop:
        Dashboard.drop_collection()
        SavedSearch.drop_collection()
    defaultDashboard = Dashboard.objects(name="Default", analystId__not__exists=1 , isPublic=True).first()
    if not defaultDashboard:
        defaultDashboard = Dashboard()
        defaultDashboard.name = "Default"
        defaultDashboard.isPublic = True
        defaultDashboard.save()
        for title in ["Counts", "Top Campaigns","Recent Indicators",
                  "Recent Emails", "Recent Samples"]:
            savedSearch = SavedSearch()
            savedSearch.name = title
            savedSearch.dashboard = defaultDashboard.id
            savedSearch.isDefaultOnDashboard = True
            savedSearch.tableColumns = getColumnsForTable(title)
            if title == "Counts":
                savedSearch.sizex = 10
            elif title == "Top Campaigns":
                savedSearch.sizex = 25
            elif title == "Counts":
                savedSearch.sizey = 13
            elif title == "Recent Indicators":
                savedSearch.row = 15
            elif title == "Recent Emails":
                savedSearch.row = 23
            elif title == "Recent Samples":
                savedSearch.row = 31
                
            savedSearch.save()
        print "Default Dashboard Created."
    else:
        print "Default Dashboard already exists."
    
def getColumnsForTable(title):
        if title == "Counts":
            colFields = ["type", "count"]
            colNames = ["Type", "Count"]
        elif  title == "Top Campaigns":
            colFields = ["name", "email_count", "indicator_count", "sample_count", 
                         "domain_count", "ip_count", "event_count", "pcap_count"]
            colNames = ["Name", "Email Count", "Indicator Count", "Sample Count", 
                         "Domain Count", "IP Count", "Event Count", "PCAP Count"]
        elif  title == "Recent Indicators":
            colFields = ["details","value", "type", "modified", "status", "source", "campaign"]
            colNames = ["Details","Value", "Type", "Added", "Status", "Source", "Campaign"]
        elif  title == "Recent Emails":
            colFields = ["details","from", "to", "subject", "isodate", "source", "campaign"]
            colNames = ["Details","From", "Recip", "Subject", "Date", "Source", "Campaign"]
        elif  title == "Recent Samples":
            colFields = ["details","filename", "size", "filetype", "created",
                          "modified", "source", "campaign"]
            colNames = ["Details","Filename", "Size", "Filetype", "Added",
                        "Modified", "Source", "Campaign"]
        columns = []
        for field, name in zip(colFields, colNames):
            if field == "details":
                size = "5%"
            else:
                size = "10%"
            col = {
                "field": field,
                "caption": name,
                "size": size,
            }
            columns.append(col)
        return columns
