from crits.actors.actor import Actor
from crits.services.analysis_result import AnalysisResult
from crits.campaigns.campaign import Campaign
from crits.certificates.certificate import Certificate
from crits.comments.comment import Comment
from crits.domains.domain import Domain
from crits.emails.email import Email
from crits.events.event import Event
from crits.indicators.indicator import Indicator
from crits.ips.ip import IP
from crits.pcaps.pcap import PCAP
from crits.raw_data.raw_data import RawData
from crits.samples.sample import Sample
from crits.screenshots.screenshot import Screenshot
from crits.targets.target import Target


def getHREFLink(object, object_type):
    """
    Creates the URL for the details button used by all object types
    """
    #comment is a special case since the link takes you to the object the comment is on 
    if object_type == "Comment":
        object_type = object["obj_type"]
    #setting the first part of the url, rawdata is the only object type thats 
    #difference from its type
    href = "/"
    if object_type == "RawData":
        href += "raw_data/"
    elif object_type == "AnalysisResult":
        href += "services/analysis_results/"
    else:
        href += object_type.lower()+"s/"
    #settings the second part of the url, screenshots and targets are the only 
    #ones that are different from being 'details'
    if object_type == "Screenshot":
        href += "render/"
    elif object_type == "Target":
        href += "info/"
        #setting key here
        key = "email_address"
    else:
        href += "details/"
    #setting the key for the last section of the url since its different for 
    #every object type
    if "url_key" in object:
        key = "url_key"
    elif object_type == "Campaign":
        key = "name"
    elif object_type == "Certificate" or object_type == "PCAP" or object_type == "Sample":
        key = "md5"
    elif object_type == "Domain":
        key = "domain"
    elif object_type == "IP":
        key = "ip"
    elif not object_type == "Target" and "_id" in object:
        key = "_id"
    else:
        key = "id"
    #adding the last part of the url 
    if key in object:
        href += unicode(object[key]) + "/"
    return href

def get_obj_name_from_title(tableTitle):
    """
    Returns the String pertaining to the type of the table. Used only 
    when editing a default dashboard table since they do not have types saved,
    it gets it from the hard-coded title.
    """
    if tableTitle == "Recent Emails":
        return "Email"
    elif tableTitle == "Recent Indicators":
        return "Indicator"
    elif tableTitle == "Recent Samples":
        return "Sample"
    elif tableTitle == "Top Backdoors":
        return "Backdoor"
    elif tableTitle == "Top Campaigns":
        return "Campaign"
    elif tableTitle == "Counts":
        return "Count"
    
def get_obj_type_from_string(objType):
    """
    Returns the Object type from the string saved to the table. This 
    is used in order to build the query to be run.
    Called by generate_search_for_saved_table and get_table_data
    """
    if objType == "Actor":
        return Actor
    elif objType == "AnalysisResult":
        return AnalysisResult
    elif objType == "Campaign":
        return Campaign
    elif objType == "Certificate":
        return Certificate
    elif objType == "Comment":
        return Comment
    elif objType == "Domain":
        return Domain
    elif objType == "Email":
        return Email
    elif objType == "Event":
        return Event
    elif objType == "Indicator":
        return Indicator
    elif objType == "IP":
        return IP
    elif objType == "PCAP":
        return PCAP
    elif objType == "RawData":
        return RawData
    elif objType == "Sample":
        return Sample
    elif objType == "Screenshot":
        return Screenshot
    elif objType == "Target":
        return Target
    return None
