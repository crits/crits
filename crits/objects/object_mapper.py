from crits.core.crits_mongoengine import EmbeddedObject

from cybox.common import String, PositiveInteger, StructuredText
from cybox.common.object_properties import CustomProperties, Property

from cybox.objects.account_object import Account
from cybox.objects.address_object import Address
from cybox.objects.api_object import API
from cybox.objects.artifact_object import Artifact
from cybox.objects.code_object import Code
from cybox.objects.custom_object import Custom
from cybox.objects.disk_object import Disk
from cybox.objects.disk_partition_object import DiskPartition
from cybox.objects.domain_name_object import DomainName
from cybox.objects.dns_query_object import DNSQuery, DNSQuestion, DNSRecord
from cybox.objects.email_message_object import EmailMessage
from cybox.objects.gui_dialogbox_object import GUIDialogbox
from cybox.objects.gui_window_object import GUIWindow
from cybox.objects.http_session_object import HTTPRequestHeaderFields
from cybox.objects.library_object import Library
from cybox.objects.memory_object import Memory
from cybox.objects.mutex_object import Mutex
from cybox.objects.network_connection_object import NetworkConnection
from cybox.objects.pipe_object import Pipe
from cybox.objects.port_object import Port
from cybox.objects.process_object import Process
from cybox.objects.system_object import System
from cybox.objects.uri_object import URI
from cybox.objects.user_account_object import UserAccount
from cybox.objects.volume_object import Volume
from cybox.objects.win_driver_object import WinDriver
from cybox.objects.win_event_object import WinEvent
from cybox.objects.win_event_log_object import WinEventLog
from cybox.objects.win_handle_object import WinHandle
from cybox.objects.win_kernel_hook_object import WinKernelHook
from cybox.objects.win_mailslot_object import WinMailslot
from cybox.objects.win_network_share_object import WinNetworkShare
from cybox.objects.win_process_object import WinProcess
from cybox.objects.win_registry_key_object import WinRegistryKey
from cybox.objects.win_service_object import WinService
from cybox.objects.win_system_object import WinSystem
from cybox.objects.win_task_object import WinTask
from cybox.objects.win_user_object import WinUser
from cybox.objects.win_volume_object import WinVolume
from cybox.objects.x509_certificate_object import X509Certificate

class UnsupportedCybOXObjectTypeError(Exception):
    """
    Exception to return if we've detected an unknown CybOX object type.
    """

    def __init__(self, type_, name, **kwargs):
        self.message = ('"%s - %s" is currently unsupported'
                   " for output to CybOX." % (type_, name))

    def __str__(self):
        return repr(self.message)

class UnsupportedCRITsObjectTypeError(Exception):
    """
    Exception to return if we've detected an unknown CRITs object type.
    """

    def __init__(self, cybox_obj, **kwargs):
        self.message = ('"%s" is currently unsupported'
                   " for input into CRITs." % (type(cybox_obj).__name__))

    def __str__(self):
        return repr(self.message)

def get_object_values(obj):
    try:
        return obj.values
    except:
        return [obj.value]

def make_cybox_object(type_, name=None, value=None):
    """
    Converts type_, name, and value to a CybOX object instance.

    :param type_: The object type.
    :type type_: str
    :param name: The object name.
    :type name: str
    :param value: The object value.
    :type value: str
    :returns: CybOX object
    """

    if type_ == "Account":
        acct = Account()
        acct.description = value
        return acct
    elif type_ == "Address":
        return Address(category=name, address_value=value)
    elif type_ == "Email Message":
        e = EmailMessage()
        e.raw_body = value
        return e
    elif type_ == "API":
        api = API()
        api.description = value
        return api
    elif type_ == "Artifact":
        if name == "Data Region":
            atype = Artifact.TYPE_GENERIC
        elif name == 'FileSystem Fragment':
            atype = Artifact.TYPE_FILE_SYSTEM
        elif name == 'Memory Region':
            atype = Artifact.TYPE_MEMORY
        else:
            raise UnsupportedCybOXObjectTypeError(type_, name)
        return Artifact(value, atype)
    elif type_ == "Code":
        obj = Code()
        obj.code_segment = value
        obj.type = name
        return obj
    elif type_ == "Disk":
        disk = Disk()
        disk.disk_name = type_
        disk.type = name
        return disk
    elif type_ == "Disk Partition":
        disk = DiskPartition()
        disk.device_name = type_
        disk.type = name
        return disk
    elif type_ == "DNS Query":
        r = URI()
        r.value = value
        dq = DNSQuestion()
        dq.qname = r
        d = DNSQuery()
        d.question = dq
        return d
    elif type_ == "DNS Record":
        # DNS Record indicators in CRITs are just a free form text box, there
        # is no good way to map them into the attributes of a DNSRecord cybox
        # object. So just stuff it in the description until someone tells me
        # otherwise.
        d = StructuredText(value=value)
        dr = DNSRecord()
        dr.description = d
        return dr
    elif type_ == "GUI Dialogbox":
        obj = GUIDialogbox()
        obj.box_text = value
        return obj
    elif type_ == "GUI Window":
        obj = GUIWindow()
        obj.window_display_name = value
        return obj
    elif type_ == "HTTP Request Header Fields" and name and name == "User-Agent":
        # TODO/NOTE: HTTPRequestHeaderFields has a ton of fields for info.
        #    we should revisit this as UI is reworked or CybOX is improved.
        obj = HTTPRequestHeaderFields()
        obj.user_agent = value
        return obj
    elif type_ == "Library":
        obj = Library()
        obj.name = value
        obj.type = name
        return obj
    elif type_ == "Memory":
        obj = Memory()
        obj.memory_source = value
        return obj
    elif type_ == "Mutex":
        m = Mutex()
        m.named = True
        m.name = String(value)
        return m
    elif type_ == "Network Connection":
        obj = NetworkConnection()
        obj.layer7_protocol = value
        return obj
    elif type_ == "Pipe":
        p = Pipe()
        p.named = True
        p.name = String(value)
        return p
    elif type_ == "Port":
        p = Port()
        try:
            p.port_value = PositiveInteger(value)
        except ValueError: # XXX: Raise a better exception...
            raise UnsupportedCybOXObjectTypeError(type_, name)
        return p
    elif type_ == "Process":
        p = Process()
        p.name = String(value)
        return p
    elif type_ == "String":
        c = Custom()
        c.custom_name = "crits:String"
        c.description = ("This is a generic string used as the value of an "
                         "Indicator or Object within CRITs.")
        c.custom_properties = CustomProperties()

        p1 = Property()
        p1.name = "value"
        p1.description = "Generic String"
        p1.value = value
        c.custom_properties.append(p1)
        return c
    elif type_ == "System":
        s = System()
        s.hostname = String(value)
        return s
    elif type_ == "URI":
        r = URI()
        r.type_ = name
        r.value = value
        return r
    elif type_ == "User Account":
        obj = UserAccount()
        obj.username = value
        return obj
    elif type_ == "Volume":
        obj = Volume()
        obj.name = value
        return obj
    elif type_ == "Win Driver":
        w = WinDriver()
        w.driver_name = String(value)
        return w
    elif type_ == "Win Event Log":
        obj = WinEventLog()
        obj.log = value
        return obj
    elif type_ == "Win Event":
        w = WinEvent()
        w.name = String(value)
        return w
    elif type_ == "Win Handle":
        obj = WinHandle()
        obj.type_ = name
        obj.object_address = value
        return obj
    elif type_ == "Win Kernel Hook":
        obj = WinKernelHook()
        obj.description = value
        return obj
    elif type_ == "Win Mailslot":
        obj = WinMailslot()
        obj.name = value
        return obj
    elif type_ == "Win Network Share":
        obj = WinNetworkShare()
        obj.local_path = value
        return obj
    elif type_ == "Win Process":
        obj = WinProcess()
        obj.window_title = value
        return obj
    elif type_ == "Win Registry Key":
        obj = WinRegistryKey()
        obj.key = value
        return obj
    elif type_ == "Win Service":
        obj = WinService()
        obj.service_name = value
        return obj
    elif type_ == "Win System":
        obj = WinSystem()
        obj.product_name = value
        return obj
    elif type_ == "Win Task":
        obj = WinTask()
        obj.name = value
        return obj
    elif type_ == "Win User Account":
        obj = WinUser()
        obj.security_id = value
        return obj
    elif type_ == "Win Volume":
        obj = WinVolume()
        obj.drive_letter = value
        return obj
    elif type_ == "X509 Certificate":
        obj = X509Certificate()
        obj.raw_certificate = value
        return obj
    """
    The following are types that are listed in the 'Indicator Type' box of
    the 'New Indicator' dialog in CRITs. These types, unlike those handled
    above, cannot be written to or read from CybOX at this point.

    The reason for the type being omitted is written as a comment inline.
    This can (and should) be revisited as new versions of CybOX are released.
    NOTE: You will have to update the corresponding make_crits_object function
    with handling for the reverse direction.

    In the mean time, these types will raise unsupported errors.
    """
    #elif type_ == "Device": # No CybOX API
    #elif type_ == "DNS Cache": # No CybOX API
    #elif type_ == "GUI": # revisit when CRITs supports width & height specification
    #elif type_ == "HTTP Session": # No good mapping between CybOX/CRITs
    #elif type_ == "Linux Package": # No CybOX API
    #elif type_ == "Network Packet": # No good mapping between CybOX/CRITs
    #elif type_ == "Network Route Entry": # No CybOX API
    #elif type_ == "Network Route": # No CybOX API
    #elif type_ == "Network Subnet": # No CybOX API
    #elif type_ == "Semaphore": # No CybOX API
    #elif type_ == "Socket": # No good mapping between CybOX/CRITs
    #elif type_ == "UNIX File": # No CybOX API
    #elif type_ == "UNIX Network Route Entry": # No CybOX API
    #elif type_ == "UNIX Pipe": # No CybOX API
    #elif type_ == "UNIX Process": # No CybOX API
    #elif type_ == "UNIX User Account": # No CybOX API
    #elif type_ == "UNIX Volume": # No CybOX API
    #elif type_ == "User Session": # No CybOX API
    #elif type_ == "Whois": # No good mapping between CybOX/CRITs
    #elif type_ == "Win Computer Account": # No CybOX API
    #elif type_ == "Win Critical Section": # No CybOX API
    #elif type_ == "Win Executable File": # No good mapping between CybOX/CRITs
    #elif type_ == "Win File": # No good mapping between CybOX/CRITs
    #elif type_ == "Win Kernel": # No CybOX API
    #elif type_ == "Win Mutex": # No good mapping between CybOX/CRITs
    #elif type_ == "Win Network Route Entry": # No CybOX API
    #elif type_ == "Win Pipe": # No good mapping between CybOX/CRITs
    #elif type_ == "Win Prefetch": # No CybOX API
    #elif type_ == "Win Semaphore": # No CybOX API
    #elif type_ == "Win System Restore": # No CybOX API
    #elif type_ == "Win Thread": # No good mapping between CybOX/CRITs
    #elif type_ == "Win Waitable Timer": # No CybOX API
    raise UnsupportedCybOXObjectTypeError(type_, name)

def make_crits_object(cybox_obj):
    """
    Converts a CybOX object instance to a CRITs EmbeddedObject instance.

    :param cybox_obj: The CybOX object.
    :type cybox_obj: CybOX object.
    :returns: :class:`crits.core.crits_mongoengine.EmbeddedObject`
    """

    o = EmbeddedObject()
    o.datatype = "string"
    if isinstance(cybox_obj, Account):
        o.object_type = "Account"
        o.value = get_object_values(cybox_obj.description)
        return o
    elif isinstance(cybox_obj, Address):
        o.object_type = "Address"
        o.name = str(cybox_obj.category)
        o.value = get_object_values(cybox_obj.address_value)
        return o
    elif isinstance(cybox_obj, API):
        o.object_type = "API"
        o.value = get_object_values(cybox_obj.description)
        return o
    elif isinstance(cybox_obj, Artifact):
        o.object_type = "Artifact"
        o.value = [cybox_obj.data]
        if cybox_obj.type_ == Artifact.TYPE_GENERIC:
            o.name = "Data Region"
            return o
        elif cybox_obj.type_ == Artifact.TYPE_FILE_SYSTEM:
            o.name = "FileSystem Fragment"
            return o
        elif cybox_obj.type_ == Artifact.TYPE_MEMORY:
            o.name = "Memory Region"
            return o
    elif isinstance(cybox_obj, Code):
        o.object_type = "Code"
        o.name = str(cybox_obj.type)
        o.value = get_object_values(cybox_obj.code_segment)
        return o
    elif isinstance(cybox_obj, Custom):
        if cybox_obj.custom_name == "crits:String":
            if cybox_obj.custom_properties[0].name == "value":
                o.object_type = "String"
                o.value = [cybox_obj.custom_properties[0].value]
                return o
    elif isinstance(cybox_obj, Disk):
        o.object_type = "Disk"
        o.name = str(cybox_obj.type)
        o.value = get_object_values(cybox_obj.disk_name)
        return o
    elif isinstance(cybox_obj, DiskPartition):
        o.object_type = "Disk Partition"
        o.name = str(cybox_obj.type)
        o.value = get_object_values(cybox_obj.device_name)
        return o
    elif isinstance(cybox_obj, DNSQuery):
        o.object_type = "DNS Query"
        o.value = get_object_values(cybox_obj.question.qname)
        return o
    elif isinstance(cybox_obj, DNSRecord):
        o.object_type = "DNS Record"
        o.value = get_object_values(cybox_obj.description)
        return o
    elif isinstance(cybox_obj, DomainName):
        o.object_type = "URI - Domain Name"
        o.value = get_object_values(cybox_obj.value)
        return o
    elif isinstance(cybox_obj, EmailMessage):
        o.object_type = "Email Message"
        o.value = [cybox_obj.raw_body]
        return o
    elif isinstance(cybox_obj, GUIDialogbox):
        o.object_type = "GUI Dialogbox"
        o.value = get_object_values(cybox_obj.box_text)
        return o
    elif isinstance(cybox_obj, GUIWindow):
        o.object_type = "GUI Window"
        o.value = get_object_values(cybox_obj.window_display_name)
        return o
    elif isinstance(cybox_obj, Library):
        o.object_type = "Library"
        o.name = str(cybox_obj.type)
        o.value = get_object_values(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, Memory):
        o.object_type = "Memory"
        o.value = get_object_values(cybox_obj.memory_source)
        return o
    elif isinstance(cybox_obj, Mutex):
        o.object_type = "Mutex"
        o.value = get_object_values(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, NetworkConnection):
        o.object_type = "Network Connection"
        o.value = get_object_values(cybox_obj.layer7_protocol)
        return o
    elif isinstance(cybox_obj, Pipe):
        o.object_type = "Pipe"
        o.value = get_object_values(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, Port):
        o.object_type = "Port"
        o.value = get_object_values(cybox_obj.port_value)
        return o
    elif isinstance(cybox_obj, Process):
        o.object_type = "Process"
        o.value = get_object_values(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, System):
        o.object_type = "System"
        o.value = get_object_values(cybox_obj.hostname)
        return o
    elif isinstance(cybox_obj, URI):
        o.object_type = "URI - URL"
        o.name = cybox_obj.type_
        o.value = get_object_values(cybox_obj.value)
        return o
    elif isinstance(cybox_obj, UserAccount):
        o.object_type = "User Account"
        o.value = get_object_values(cybox_obj.username)
        return o
    elif isinstance(cybox_obj, Volume):
        o.object_type = "Volume"
        o.value = get_object_values(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, WinDriver):
        o.object_type = "Win Driver"
        o.value = get_object_values(cybox_obj.driver_name)
        return o
    elif isinstance(cybox_obj, WinEventLog):
        o.object_type = "Win Event Log"
        o.value = get_object_values(cybox_obj.log)
        return o
    elif isinstance(cybox_obj, WinEvent):
        o.object_type = "Win Event"
        o.value = get_object_values(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, WinHandle):
        o.object_type = "Win Handle"
        o.name = str(cybox_obj.type_)
        o.value = get_object_values(cybox_obj.object_address)
        return o
    elif isinstance(cybox_obj, WinKernelHook):
        o.object_type = "Win Kernel Hook"
        o.value = get_object_values(cybox_obj.description)
        return o
    elif isinstance(cybox_obj, WinMailslot):
        o.object_type = "Win Mailslot"
        o.value = get_object_values(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, WinNetworkShare):
        o.object_type = "Win Network Share"
        o.value = get_object_values(cybox_obj.local_path)
        return o
    elif isinstance(cybox_obj, WinProcess):
        o.object_type = "Win Process"
        o.value = get_object_values(cybox_obj.window_title)
        return o
    elif isinstance(cybox_obj, WinRegistryKey):
        o.object_type = "Win Registry Key"
        o.value = get_object_values(cybox_obj.key)
        return o
    elif isinstance(cybox_obj, WinService):
        o.object_type = "Win Service"
        o.value = get_object_values(cybox_obj.service_name)
        return o
    elif isinstance(cybox_obj, WinSystem):
        o.object_type = "Win System"
        o.value = get_object_values(cybox_obj.product_name)
        return o
    elif isinstance(cybox_obj, WinTask):
        o.object_type = "Win Task"
        o.value = get_object_values(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, WinUser):
        o.object_type = "Win User Account"
        o.value = get_object_values(cybox_obj.security_id)
        return o
    elif isinstance(cybox_obj, WinVolume):
        o.object_type = "Win Volume"
        o.value = get_object_values(cybox_obj.drive_letter)
        return o
    elif isinstance(cybox_obj, X509Certificate):
        o.object_type = "X509 Certificate"
        o.value = get_object_values(cybox_obj.raw_certificate)
        return o
    raise UnsupportedCRITsObjectTypeError(cybox_obj)
