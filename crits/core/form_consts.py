class Common():
    ADD_INDICATOR = "Add Indicator?"
    BUCKET_LIST = "Bucket List"
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
    Campaign = "Campaign"
    Certificate = "Certificate"
    Disassembly = "Disassembly"
    Domain = "Domain"
    Email = "Email"
    Event = "Event"
    Indicator = "Indicator"
    IP = "IP"
    Object = "Object"
    PCAP = "PCAP"
    RawData = "RawData"
    Sample = "Sample"
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
    Constants for Campaigns.
    """

    NAME = "Name"
    ALIASES = "Aliases"
    DESCRIPTION = "Description"
    CAMPAIGN = "Campaign"
    CAMPAIGN_CONFIDENCE = "Campaign Confidence"
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
    CAMPAIGN = "Campaign"
    CAMPAIGN_CONFIDENCE = "Campaign Confidence"
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

class Disassembly():
    """
    Constants for Disassembly.
    """

    SOURCE = Common.SOURCE


class Domain():
    """
    Constants for Domains.
    """

    DOMAIN_NAME = "Domain Name"
    CAMPAIGN = "Campaign"
    CAMPAIGN_CONFIDENCE = "Campaign Confidence"
    DOMAIN_SOURCE = Common.SOURCE
    DOMAIN_METHOD = Common.SOURCE_METHOD
    DOMAIN_REFERENCE = Common.SOURCE_REFERENCE
    ADD_IP_ADDRESS = "Add IP Address?"
    IP_ADDRESS = IP.IP_ADDRESS
    IP_DATE = IP.IP_DATE
    SAME_SOURCE = "Use Domain Source"
    IP_SOURCE = IP.IP_SOURCE
    IP_METHOD = IP.IP_METHOD
    IP_REFERENCE = IP.IP_REFERENCE
    ADD_INDICATOR = Common.ADD_INDICATOR

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
    CAMPAIGN = "Campaign"
    CAMPAIGN_CONFIDENCE = "Campaign Confidence"
    EMAIL_RESULTS = "Email Me Results"
    FILE_DATA = "File Data"
    FILE_FORMAT = "File Format"
    FILE_NAME = "File Name"
    INHERIT_CAMPAIGNS = "Inherit Campaigns?"
    INHERIT_SOURCES = "Inherit Sources?"
    MD5 = "MD5"
    RELATED_MD5 = "Related MD5"
    PASSWORD = "Password"
    SOURCE = Common.SOURCE
    SOURCE_METHOD = Common.SOURCE_METHOD
    SOURCE_REFERENCE = Common.SOURCE_REFERENCE
    UPLOAD_TYPE = "Upload Type"

    CACHED_RESULTS = "sample_cached_results"

    class UploadType():
        FILE_UPLOAD = "File Upload"
        METADATA_UPLOAD = "Metadata Upload"


class Target():
    """
    Constants for Targets.
    """

    TITLE = "Title"


def get_source_field_for_class(otype):
    """
    Based on the CRITs type, get the source field constant.

    :param otype: The CRITs type.
    :type otype: str.
    :returns: str
    """

    class_to_source_field_map = {
        Common.Certificate: Certificate.SOURCE,
        Common.Disassembly: Disassembly.SOURCE,
        Common.Domain: Domain.DOMAIN_SOURCE,
        Common.Email: Email.SOURCE,
        Common.Event: Event.SOURCE,
        Common.Indicator: Indicator.SOURCE,
        Common.IP: IP.SOURCE,
        Common.Object: Object.SOURCE,
        Common.PCAP: PCAP.SOURCE,
        Common.RawData: RawData.SOURCE,
        Common.Sample: Sample.SOURCE
    }
    return class_to_source_field_map.get(otype)
