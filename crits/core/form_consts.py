class Action():
    ACTION_TYPE = "Action type"
    BEGIN_DATE = "Begin date"
    ANALYST = "Analyst"
    END_DATE = "End date"
    PERFORMED_DATE = "Performed date"
    ACTIVE = "Active"
    REASON = "Reason"
    DATE = "Date"
    OBJECT_TYPES = "TLOs"
    PREFERRED = "Preferred TLOs"

class Common():
    ADD_INDICATOR = "Add Indicator?"
    BUCKET_LIST = "Bucket List"
    CAMPAIGN = "Campaign"
    CAMPAIGN_CONFIDENCE = "Campaign Confidence"
    OBJECTS_DATA = "Objects Data"
    SOURCE = "Source"
    SOURCE_REFERENCE = "Source Reference"
    SOURCE_METHOD = "Source Method"
    TICKET = "Ticket"

    CLASS_ATTRIBUTE = "class"

    BULK_SKIP = "bulkskip"
    BULK_REQUIRED = "bulkrequired"

    # class names
    Actor = "Actor"
    Backdoor = "Backdoor"
    Campaign = "Campaign"
    Certificate = "Certificate"
    Domain = "Domain"
    Email = "Email"
    Event = "Event"
    Exploit = "Exploit"
    Indicator = "Indicator"
    IP = "IP"
    Object = "Object"
    PCAP = "PCAP"
    RawData = "RawData"
    Sample = "Sample"
    Signature = "Signature"
    Target = "Target"

    BUCKET_LIST_VARIABLE_NAME = "bucket_list"
    TICKET_VARIABLE_NAME = "ticket"

class Status():
    """
    Status fields/enumerations used in bulk upload.
    """

    STATUS_FIELD = "status";
    FAILURE = 0;
    SUCCESS = 1;
    DUPLICATE = 2;


class Actor():
    """
    Constants for Actors.
    """

    NAME = "Name"
    ALIASES = "Aliases"
    DESCRIPTION = "Description"
    CAMPAIGN = Common.CAMPAIGN
    CAMPAIGN_CONFIDENCE = Common.CAMPAIGN_CONFIDENCE
    SOURCE = Common.SOURCE
    SOURCE_METHOD = "Source Method"
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE


class Backdoor():
    """
    Constants for Backdoors.
    """

    NAME = "Backdoor name"
    ALIASES = "Aliases"
    DESCRIPTION = "Description"
    CAMPAIGN = Common.CAMPAIGN
    CAMPAIGN_CONFIDENCE = Common.CAMPAIGN_CONFIDENCE
    VERSION = "Version"
    SOURCE = Common.SOURCE
    SOURCE_METHOD = "Source Method"
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE


class Exploit():
    """
    Constants for Exploits.
    """

    NAME = "Name"
    DESCRIPTION = "Description"
    CVE = "CVE"
    CAMPAIGN = Common.CAMPAIGN
    CAMPAIGN_CONFIDENCE = Common.CAMPAIGN_CONFIDENCE
    VERSION = "Version"
    SOURCE = Common.SOURCE
    SOURCE_METHOD = "Source Method"
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE


class Campaign():
    """
    Constants for Campaigns.
    """

    NAME = "Name"


class Certificate():
    """
    Constants for Certificates.
    """

    SOURCE = Common.SOURCE
    SOURCE_METHOD = Common.SOURCE_METHOD
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE


class IP():
    """
    Constants for IPs.
    """

    IP_ADDRESS = "IP Address"
    IP_TYPE = "IP Type"
    ANALYST = "Analyst"
    CAMPAIGN = Common.CAMPAIGN
    CAMPAIGN_CONFIDENCE = Common.CAMPAIGN_CONFIDENCE
    SOURCE = Common.SOURCE
    SOURCE_METHOD = Common.SOURCE_METHOD
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE
    ADD_INDICATOR = Common.ADD_INDICATOR
    INDICATOR_REFERENCE = "Indicator Reference"

    IP_DATE = "IP Date"
    IP_SOURCE = "IP Source"
    IP_METHOD = "IP Source Method"
    IP_REFERENCE = "IP Source Reference"
    CACHED_RESULTS = "ip_cached_results"


class Domain():
    """
    Constants for Domains.
    """

    DOMAIN_NAME = "Domain Name"
    CAMPAIGN = Common.CAMPAIGN
    CAMPAIGN_CONFIDENCE = Common.CAMPAIGN_CONFIDENCE
    DOMAIN_SOURCE = Common.SOURCE
    DOMAIN_METHOD = Common.SOURCE_METHOD
    DOMAIN_REFERENCE = Common.SOURCE_REFERENCE
    ADD_IP_ADDRESS = "Add IP Address?"
    IP_ADDRESS = IP.IP_ADDRESS
    IP_TYPE = IP.IP_TYPE
    IP_DATE = IP.IP_DATE
    SAME_SOURCE = "Use Domain Source"
    IP_SOURCE = IP.IP_SOURCE
    IP_METHOD = IP.IP_METHOD
    IP_REFERENCE = IP.IP_REFERENCE
    ADD_INDICATORS = "Add Indicator(s)?"

    CACHED_RESULTS = "domain_cached_results"

class Email():
    """
    Constants for Emails.
    """

    SOURCE = Common.SOURCE
    SOURCE_METHOD = Common.SOURCE_METHOD
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE


class Event():
    """
    Constants for Events.
    """

    TITLE = "Title"
    SOURCE = Common.SOURCE
    SOURCE_METHOD = Common.SOURCE_METHOD
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE


class Indicator():
    """
    Constants for Indicators.
    """

    SOURCE = Common.SOURCE
    SOURCE_METHOD = Common.SOURCE_METHOD
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE


class NotificationType():
    ALERT = 'alert'
    ERROR = 'error'
    INFORMATION = 'information'
    NOTIFICATION = 'notification'
    SUCCESS = 'success'
    WARNING = 'warning'

    ALL = [ALERT, ERROR, INFORMATION, NOTIFICATION, SUCCESS, WARNING]


class Object():
    """
    Constants for Objects.
    """

    OBJECT_TYPE_INDEX = 0
    VALUE_INDEX = 1
    SOURCE_INDEX = 2
    METHOD_INDEX = 3
    REFERENCE_INDEX = 4
    ADD_INDICATOR_INDEX = 5

    OBJECT_TYPE = "Object Type"
    VALUE = "Value"
    SOURCE = Common.SOURCE
    METHOD = "Method"
    REFERENCE = "Reference"
    PARENT_OBJECT_TYPE = "Otype"
    PARENT_OBJECT_ID = "Oid"
    ADD_INDICATOR = Common.ADD_INDICATOR


class PCAP():
    """
    Constants for PCAPs.
    """

    SOURCE = Common.SOURCE
    SOURCE_METHOD = Common.SOURCE_METHOD
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE


class RawData():
    """
    Constants for RawData.
    """

    SOURCE = Common.SOURCE
    SOURCE_METHOD = Common.SOURCE_METHOD
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE


class Sample():
    """
    Constants for Samples.
    """

    BUCKET_LIST = Common.BUCKET_LIST
    CAMPAIGN = Common.CAMPAIGN
    CAMPAIGN_CONFIDENCE = Common.CAMPAIGN_CONFIDENCE
    EMAIL_RESULTS = "Email Me Results"
    FILE_DATA = "File Data"
    FILE_FORMAT = "File Format"
    FILE_NAME = "File Name"
    INHERIT_CAMPAIGNS = "Inherit Campaigns?"
    INHERIT_SOURCES = "Inherit Sources?"
    MD5 = "MD5"
    MIMETYPE = "Mimetype"
    RELATED_MD5 = "Related MD5"
    PASSWORD = "Password"
    SHA1 = "SHA1"
    SHA256 = "SHA256"
    SIZE = "SIZE"
    SOURCE = Common.SOURCE
    SOURCE_METHOD = Common.SOURCE_METHOD
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE
    UPLOAD_TYPE = "Upload Type"

    CACHED_RESULTS = "sample_cached_results"

    class UploadType():
        FILE_UPLOAD = "File Upload"
        METADATA_UPLOAD = "Metadata Upload"

class Signature():
    """
    Constants for Signature. Dependencies as list? Similar to bucket list, but not in other classes
    """

    SOURCE = Common.SOURCE
    SOURCE_METHOD = Common.SOURCE_METHOD
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE

class Target():
    """
    Constants for Targets.
    """

    TITLE = "Title"
    CAMPAIGN = Common.CAMPAIGN
    CAMPAIGN_CONFIDENCE = Common.CAMPAIGN_CONFIDENCE



def get_source_field_for_class(otype):
    """
    Based on the CRITs type, get the source field constant.

    :param otype: The CRITs type.
    :type otype: str.
    :returns: str
    """

    class_to_source_field_map = {
        Common.Certificate: Certificate.SOURCE,
        Common.Domain: Domain.DOMAIN_SOURCE,
        Common.Email: Email.SOURCE,
        Common.Event: Event.SOURCE,
        Common.Indicator: Indicator.SOURCE,
        Common.IP: IP.SOURCE,
        Common.Object: Object.SOURCE,
        Common.PCAP: PCAP.SOURCE,
        Common.RawData: RawData.SOURCE,
        Common.Sample: Sample.SOURCE,
        Common.Signature: Signature.SOURCE,
    }
    return class_to_source_field_map.get(otype)
