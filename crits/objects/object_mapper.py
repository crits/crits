from crits.core.crits_mongoengine import EmbeddedObject

from cybox.common import String, PositiveInteger

from cybox.objects.account_object import Account
from cybox.objects.address_object import Address
from cybox.objects.api_object import API
from cybox.objects.artifact_object import Artifact
from cybox.objects.disk_object import Disk
from cybox.objects.disk_partition_object import DiskPartition
from cybox.objects.dns_query_object import DNSQuery, DNSQuestion, DNSRecord
from cybox.objects.email_message_object import EmailMessage
from cybox.objects.gui_dialogbox_object import GUIDialogbox
from cybox.objects.gui_object import GUI
from cybox.objects.gui_window_object import GUIWindow
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
                   " for input into CRITs." % (cybox_obj))

    def __str__(self):
        return repr(self.message)

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

    if type_ == "Address":
        return Address(category=name, address_value=value)
    elif type_ == "Email Message":
        e = EmailMessage()
        e.raw_body = value
        return e
    elif type_ == "URI":
        r = URI()
        r.type_ = name
        r.value = value
        return r
    elif type_ == "Account":
    acct = Account()
    acct.description = value
        return acct
    elif type_ == "API":
    api = API()
    api.description = value
    api.function_name = name
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
    elif type_ == "Disk":
    disk = Disk()
    disk.disk_name = name
    disk.type = type_
    return disk
    elif type_ == "Disk Partition":
    disk = DiskPartition()
    disk.device_name = name
    disk.type = type_
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
    obj.box_caption = name
    obj.box_text = value
    return obj
    elif type_ == "GUI": # TODO REPR
    obj = GUI()
    obj.width = name
    obj.height = value
    return obj
    elif type_ == "GUI Window":
    obj = GUIWindow()
    obj.window_display_name = name
    return obj
    elif type_ == "Library":
        obj = Library()
    obj.name = name
    obj.type = value
    return obj
    elif type_ == "Memory":
        obj = Memory()
    obj.name = name
    obj.memory_source = value
    return obj
    elif type_ == "Mutex":
        m = Mutex()
        m.named = True
        m.name = String(value)
        return m
    elif type_ == "Network Connection":
        obj = NetworkConnection()
    obj.layer7_protocol = name
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
        # There are lots of attributes to a Process, let's use "name".
        p = Process()
        p.name = String(value)
        return p
    elif type_ == "String":
    return String(value)
    elif type_ == "System":
        # Another place where there are lots of attributes to a System.
        # I'm picking hostname and sticking to it.
        s = System()
        s.hostname = String(value)
        return s
    elif type_ == "User Account":
        obj = UserAccount()
    obj.username = value
    return obj
    elif type_ == "Volume":
    obj = Volume()
    obj.name = name
    obj.file_system_type = value
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
    obj.name = value
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
    elif type_ == "Win Volume":
    obj = WinVolume()
    obj.drive_letter = value
    return obj
    elif type_ == "X509 Certificate":
    obj = X509Certificate()
    obj.raw_certificate = value
    return obj
    elif type_ == "Code": # TODO cybox-unavailable
        pass
    elif type_ == "Device": # TODO cybox-unavailable
        pass
    elif type_ == "DNS Cache": # TODO cybox-unavailable
        pass
    elif type_ == "File": # TODO REPR
        pass
    elif type_ == "HTTP Session": #TODO REPR
        # HTTPSession.http_request_response is a list of HTTPRequestResponse
        # objects.

        # HTTPRequestResponse objects have two attributes:
        # http_client_request (type: HTTPClientRequest)
        # http_server_response (type: HTTPServerResponse)

        # HTTPClientRequest objects have three attributes:
        # http_request_line (type: HTTPRequestLine)
        # http_request_header (type: HTTPRequestHeader)
        # http_message_body (type: HTTPMessage)

        # HTTPRequestLine objects have three attributes:
        # http_method (type: String (the cybox kind))
        # value (type: String (the cybox kind))
        # version (type: String (the cybox kind))

        # HTTPRequestHeader has two attributes:
        # raw_header (type: String (the cybox kind))
        # parsed_header (type: HTTPRequestHeaderFields)

        # HTTPMessage has two attributes:
        # length (type: PositiveInteger)
        # message_body (type: String (the cybox kind))

        # HTTPRequestHeaderFields have a crap-ton of attributes. All of which
        # are just random HTTP header names. Most are of type String (the
        # cybox kind) but some (content_length) are of type Integer (the
        # cybox kind), from_ (Address), date (DateTime (probably a cybox thing)
        # host (HostField), referer (URI), dnt (URI, WTF?) and random other
        # things.

        # As near as I can tell HTTPServerResponse objects are the same
        # structure as an HTTPClientRequest with minor differences. For
        # example, an HTTPServerResponse has an HTTPStatusLine in place of
        # the HTTPRequestLine.
        pass # XXX: We shouldn't support this.
    elif type_ == "HTTP Request Header Fields": # TODO REPR
        pass
    elif type_ == "Linux Package": # TODO cybox-unavailable
        pass
    elif type_ == "Network Flow": # TODO cybox-unavailable
        pass
    elif type_ == "Network Packet": # TODO REPR
        pass
    elif type_ == "Network Route Entry": # TODO cybox-unavailable
        pass
    elif type_ == "Network Route": # TODO cybox-unavailable
        pass
    elif type_ == "Network Subnet": # TODO cybox-unavailable
        pass
    elif type_ == "Semaphore": # TODO cybox-unavailable
        pass
    elif type_ == "Socket": # TODO REPR
        pass
    elif type_ == "UNIX File": # TODO cybox-unavailable
        pass
    elif type_ == "UNIX Network Route Entry": # TODO cybox-unavailable
        pass
    elif type_ == "UNIX Pipe": # TODO cybox-unavailable
        pass
    elif type_ == "UNIX Process": # TODO cybox-unavailable
        pass
    elif type_ == "UNIX User Account": # TODO cybox-unavailable
        pass
    elif type_ == "UNIX Volume": # TODO cybox-unavailable
        pass
    elif type_ == "User Session": # TODO cybox-unavailable
        pass
    elif type_ == "Whois": # TODO REPR
        pass
    elif type_ == "Win Computer Account": # TODO cybox-unavailable
        pass
    elif type_ == "Win Critical Section": # TODO cybox-unavailable
        pass
    elif type_ == "Win Executable File": # TODO REPR
        pass
    elif type_ == "Win File": # TODO REPR
        pass
    elif type_ == "Win Kernel": # TODO cybox-unavailable
        pass 
    elif type_ == "Win Mutex": # TODO REPR
        pass
    elif type_ == "Win Network Route Entry": # TODO cybox-unavailable
        pass
    elif type_ == "Win Pipe": # TODO REPR
        pass
    elif type_ == "Win Prefetch": # TODO cybox-unavailable
        pass
    elif type_ == "Win Semaphore": # TODO cybox-unavailable
        pass
    elif type_ == "Win System Restore": # TODO cybox-unavailable
        pass
    elif type_ == "Win Thread": # TODO REPR
        pass
    elif type_ == "Win User Account": # TODO REPR
        pass
    elif type_ == "Win Waitable Timer": # TODO cybox-unavailable
        pass
    raise UnsupportedCybOXObjectTypeError(type_, name)

def make_crits_object(cybox_obj):
    """
    Converts a CybOX object instance to a CRITs EmbeddedObject instance.

    :param cybox_obj: The CybOX object.
    :type cybox_obj: CybOX object.
    :returns: :class:`crits.core.crits_mongoengine.EmbeddedObject`
    """

    o = EmbeddedObject()
    if isinstance(cybox_obj, Address):
        o.datatype = "string"
        o.object_type = "Address"
        o.name = str(cybox_obj.category)
        o.value = str(cybox_obj.address_value)
        return o
    elif isinstance(cybox_obj, URI):
        o.datatype = "string"
        o.object_type = "URI"
        o.name = str(cybox_obj.type_)
        o.value = str(cybox_obj.value)
        return o
    elif isinstance(cybox_obj, EmailMessage):
        o.datatype = "string"
        o.object_type = "Email Message"
        o.name = str(cybox_obj.type_)
        o.value = str(cybox_obj.value)
        return o
    elif isinstance(cybox_obj, Account):
        o.datatype = "string"
        o.object_type = "Account"
        o.name = str(cybox_obj.type_)
        o.value = str(cybox_obj.description)
        return o
    elif isinstance(cybox_obj, API):
        o.datatype = "string"
        o.object_type = "API"
        o.name = str(cybox_obj.function_name)
        o.value = str(cybox_obj.description)
        return o
    elif isinstance(cybox_obj, Artifact):
        o.datatype = "string"
        o.object_type = "Artifact"
    o.value = str(cybox_obj.data)
        if cybox_obj.type_ == Artifact.TYPE_GENERIC:
        o.name = "Data Region"
        return o
        elif cybox_obj.type_ == Artifact.TYPE_FILE_SYSTEM:
        o.name = "FileSystem Fragment"
        return o
        elif cybox_obj.type_ == Artifact.TYPE_MEMORY:
        o.name = "Memory Region"
        return o
    elif isinstance(cybox_obj, Disk):
        o.datatype = "string"
        o.object_type = "Disk"
        o.name = str(cybox_obj.disk_name)
        return o
    elif isinstance(cybox_obj, DiskPartition):
        o.datatype = "string"
        o.object_type = "Disk Partition"
        o.name = str(cybox_obj.device_name)
        return o
    elif isinstance(cybox_obj, DNSQuery):
        o.datatype = "string"
        o.object_type = "DNS Query"
        o.value = str(cybox_obj.question.qname.value)
        return o
    elif isinstance(cybox_obj, DNSRecord):
        o.datatype = "string"
        o.object_type = "DNS Record"
        o.value = str(cybox_obj.description)
        return o
    elif isinstance(cybox_obj, GUIDialogbox):
        o.datatype = "string"
        o.object_type = "GUI Dialogbox"
        o.value = str(cybox_obj.box_text)
        return o
    elif isinstance(cybox_obj, GUIWindow):
        o.datatype = "string"
        o.object_type = "GUI Window"
        o.value = str(cybox_obj.display_name)
        return o
    elif isinstance(cybox_obj, Library):
        o.datatype = "string"
        o.object_type = "Library"
        o.value = str(cybox_obj.type)
        return o
    elif isinstance(cybox_obj, Memory):
        o.datatype = "string"
        o.object_type = "Memory"
        o.value = str(cybox_obj.memory_source)
        return o
    elif isinstance(cybox_obj, Mutex):
        o.datatype = "string"
        o.object_type = "Mutex"
        o.value = str(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, NetworkConnection):
        o.datatype = "string"
        o.object_type = "Network Connection"
        o.value = str(cybox_obj.layer7_protocol)
        return o
    elif isinstance(cybox_obj, Pipe):
        o.datatype = "string"
        o.object_type = "Pipe"
        o.value = str(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, Port):
        o.datatype = "string"
        o.object_type = "Port"
        o.value = str(cybox_obj.port_value)
        return o
    elif isinstance(cybox_obj, Process):
        o.datatype = "string"
        o.object_type = "Process"
        o.value = str(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, String):
        o.datatype = "string"
        o.object_type = "String"
        o.value = str(cybox_obj.value)
        return o
    elif isinstance(cybox_obj, System):
        o.datatype = "string"
        o.object_type = "System"
        o.value = str(cybox_obj.hostname)
        return o
    elif isinstance(cybox_obj, UserAccount):
        o.datatype = "string"
        o.object_type = "User Account"
        o.value = str(cybox_obj.username)
        return o
    elif isinstance(cybox_obj, Volume):
        o.datatype = "string"
        o.object_type = "Volume"
        o.value = str(cybox_obj.file_system_type)
        return o
    elif isinstance(cybox_obj, WinDriver):
        o.datatype = "string"
        o.object_type = "Win Driver"
        o.value = str(cybox_obj.driver_name)
        return o
    elif isinstance(cybox_obj, WinEventLog):
        o.datatype = "string"
        o.object_type = "Win Event Log"
        o.value = str(cybox_obj.log)
        return o
    elif isinstance(cybox_obj, WinEvent):
        o.datatype = "string"
        o.object_type = "Win Event"
        o.value = str(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, WinHandle):
        o.datatype = "string"
        o.object_type = "Win Handle"
        o.value = str(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, WinKernelHook):
        o.datatype = "string"
        o.object_type = "Win Kernel Hook"
        o.value = str(cybox_obj.description)
        return o
    elif isinstance(cybox_obj, WinMailslot):
        o.datatype = "string"
        o.object_type = "Win Mailslot"
        o.value = str(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, WinNetworkShare):
        o.datatype = "string"
        o.object_type = "Win Network Share"
        o.value = str(cybox_obj.local_path)
        return o
    elif isinstance(cybox_obj, WinProcess):
        o.datatype = "string"
        o.object_type = "Win Process"
        o.value = str(cybox_obj.window_title)
        return o
    elif isinstance(cybox_obj, WinRegistryKey):
        o.datatype = "string"
        o.object_type = "Win Registry Key"
        o.value = str(cybox_obj.key)
        return o
    elif isinstance(cybox_obj, WinService):
        o.datatype = "string"
        o.object_type = "Win Service"
        o.value = str(cybox_obj.service_name)
        return o
    elif isinstance(cybox_obj, WinSystem):
        o.datatype = "string"
        o.object_type = "Win System"
        o.value = str(cybox_obj.product_name)
        return o
    elif isinstance(cybox_obj, WinTask):
        o.datatype = "string"
        o.object_type = "Win Task"
        o.value = str(cybox_obj.name)
        return o
    elif isinstance(cybox_obj, WinVolume):
        o.datatype = "string"
        o.object_type = "Win Volume"
        o.value = str(cybox_obj.drive_letter)
        return o
    elif isinstance(cybox_obj, X509Certificate):
        o.datatype = "string"
        o.object_type = "X509 Certificate"
        o.value = str(cybox_obj.raw_certificate)
        return o
    raise UnsupportedCRITsObjectTypeError(cybox_obj)
