from django.core.management.base import BaseCommand

from crits.objects.object_type import ObjectType

class Command(BaseCommand):
    """
    Script Class.
    """

    help = 'Creates object types in MongoDB.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        add_object_types(True)

def add_object_types(drop=False):
    """
    Add Object Types to the system.

    :param drop: Drop the collection before adding.
    :type drop: boolean
    """

    types = [
        ("Account", False, None, False, "The Account object is intended to characterize generic accounts.", 'string'),
        ("Address", True, "Category", True, "The Address object is intended to specify a cyber address.", "asn", 'string'),
        ("Address", True, "Category", True, "The Address object is intended to specify a cyber address.", "atm", 'string'),
        ("Address", True, "Category", True, "The Address object is intended to specify a cyber address.", "cidr", 'string'),
        ("Address", True, "Category", True, "The Address object is intended to specify a cyber address.", "e-mail", 'string'),
        ("Address", True, "Category", True, "The Address object is intended to specify a cyber address.", "mac", 'string'),
        ("Address", True, "Category", True, "The Address object is intended to specify a cyber address.", "ipv4-addr", 'string'),
        ("Address", True, "Category", True, "The Address object is intended to specify a cyber address.", "ipv4-net", 'string'),
        ("Address", True, "Category", True, "The Address object is intended to specify a cyber address.", "ipv4-net-mask", 'string'),
        ("Address", True, "Category", True, "The Address object is intended to specify a cyber address.", "ipv6-addr", 'string'),
        ("Address", True, "Category", True, "The Address object is intended to specify a cyber address.", "ipv6-net", 'string'),
        ("Address", True, "Category", True, "The Address object is intended to specify a cyber address.", "ipv6-net-mask", 'string'),
        ("Address", True, "Category", True, "The Address object is intended to specify a cyber address.", "ext-value", 'string'),
        ("API", False, None, False, "The API object is intended to characterize a single Application Programming Interface.", 'string'),
        ("Artifact", True, "Type", True, "The Artifact object is intended to encapsulate and convey the content of a Raw Artifact.", "File", 'file'),
        ("Artifact", True, "Type", True, "The Artifact object is intended to encapsulate and convey the content of a Raw Artifact.", "Memory Region", 'bigstring'),
        ("Artifact", True, "Type", True, "The Artifact object is intended to encapsulate and convey the content of a Raw Artifact.", "FileSystem Fragment", 'bigstring'),
        ("Artifact", True, "Type", True, "The Artifact object is intended to encapsulate and convey the content of a Raw Artifact.", "Network Traffic", 'file'),
        ("Artifact", True, "Type", True, "The Artifact object is intended to encapsulate and convey the content of a Raw Artifact.", "Data Region", 'bigstring'),
        ("Code", True, "Type", True, "The Code object is intended to characterize a body of computer code.", "Source_Code", 'bigstring'),
        ("Code", True, "Type", True, "The Code object is intended to characterize a body of computer code.", "Byte_Code", 'bigstring'),
        ("Code", True, "Type", True, "The Code object is intended to characterize a body of computer code.", "Binary_Code", 'bigstring'),
        ("Device", False, None, None, "The Device_Object object is intended to characterize a specific Device.", 'string'),
        ("Disk", True, "Type", True, "The Disk object is intended to characterize a disk drive.", "Removable", 'string'),
        ("Disk", True, "Type", True, "The Disk object is intended to characterize a disk drive.", "Fixed", 'string'),
        ("Disk", True, "Type", True, "The Disk object is intended to characterize a disk drive.", "Remote", 'string'),
        ("Disk", True, "Type", True, "The Disk object is intended to characterize a disk drive.", "CDRom", 'string'),
        ("Disk", True, "Type", True, "The Disk object is intended to characterize a disk drive.", "RAMDisk", 'string'),
        ("Disk Partition", False, None, False, "The Disk_Partition object is intended to characterize a single partition of a disk drive.", 'string'),
        ("DNS Cache", False, None, False, "The DNS_Cache object is intended to characterize a domain name system cache.", 'string'),
        ("DNS Query", False, None, False, "The DNS_Query object is intended to represent a single DNS query.", 'string'),
        ("DNS Record", False, None, False, "The DNS object is intended to characterize an individual DNS record.", 'bigstring'),
        ("Email Message", False, None, False, "The Email_Message object is intended to characterize an individual email message.", 'bigstring'),
        ("File", False, None, False, "The File object is intended to characterize a generic file.", 'file'),
        ("GUI Dialogbox", False, None, False, "The GUI_Dialogbox object is intended to characterize GUI dialog boxes.", 'string'),
        ("GUI", False, None, False, "The GUI_Object object is intended to charaterize generic GUI objects.", 'string'),
        ("GUI Window", False, None, False, "The GUI_Window object is intended to characterize GUI windows.", 'string'),
        ("HTTP Session", False, None, False, "The HTTP_Session object is intended to capture the HTTP requests and responses made on a single HTTP session.", 'bigstring'),
        ("HTTP Request Header Fields", True, "Type", True, "The HTTP Request Header Fields captures parsed HTTP request header fields.", "User-Agent", 'string'),
        ("Library", True, "Type", True, "The Library object is intended to characterize software libraries.", "Dynamic", 'bigstring'),
        ("Library", True, "Type", True, "The Library object is intended to characterize software libraries.", "Static", 'bigstring'),
        ("Library", True, "Type", True, "The Library object is intended to characterize software libraries.", "Remote", 'bigstring'),
        ("Library", True, "Type", True, "The Library object is intended to characterize software libraries.", "Shared", 'bigstring'),
        ("Library", True, "Type", True, "The Library object is intended to characterize software libraries.", "Other", 'bigstring'),
        ("Linux Package", False, None, False, "The Linux_Package object is intended to characterize a Linux package.", 'bigstring'),
        ("Memory", False, None, False, "The Memory_Region object is intended to characterize generic memory objects.", 'bigstring'),
        ("Mutex", False, None, False, "The Mutex object is intended to characterize generic mutual exclusion (mutex) objects.", 'bigstring'),
        ("Network Connection", False, None, False, "The Network_Connection object is intended to represent a single network connection.", 'bigstring'),
        ("Network Flow", False, None, False, "The Network_Flow_Object object is intended to represent a single network traffic flow.", 'file'),
        ("Network Packet", False, None, False, "The Network_Packet_Object is intended to represent a single network packet.", 'bigstring'),
        ("Network Route Entry", False, None, False, "The Network_Route_Entry object is intended to characterize generic system network routing table entries.", 'string'),
        ("Network Route", False, None, False, "The Network_Route_Object object is intended to specify a single network route.", 'string'),
        ("Network Subnet", False, None, False, "The Network_Subnet object is intended to characterize a generic system network subnet.", 'string'),
        ("Pipe", False, None, False, "The Pipe object is intended to characterize generic system pipes.", 'string'),
        ("Port", False, None, False, "The Port object is intended to characterize networking ports.", 'string'),
        ("Process", False, None, False, "The Process object is intended to characterize system processes.", 'string'),
        ("Semaphore", False, None, False, "The Semaphore object is intended to characterize generic semaphore objects.", 'string'),
        ("Socket", True, "Type", True, "The Socket object is intended to characterize network sockets.", "SOCK_STREAM", 'string'),
        ("Socket", True, "Type", True, "The Socket object is intended to characterize network sockets.", "SOCK_DGRAM", 'string'),
        ("Socket", True, "Type", True, "The Socket object is intended to characterize network sockets.", "SOCK_RAW", 'string'),
        ("Socket", True, "Type", True, "The Socket object is intended to characterize network sockets.", "SOCK_RDM", 'string'),
        ("Socket", True, "Type", True, "The Socket object is intended to characterize network sockets.", "SOCK_SEQPACKET", 'string'),
        ("String", False, None, False, "The String object is intended to characterize generic string objects.", 'bigstring'),
        ("System", False, None, False, "The System object is intended to characterize computer systems (as a combination of both software and hardware).", 'string'),
        ("UNIX File", True, "Type", True, "The Unix_File object is intended to characterize Unix files.", "regularfile", 'string'),
        ("UNIX File", True, "Type", True, "The Unix_File object is intended to characterize Unix files.", "directory", 'string'),
        ("UNIX File", True, "Type", True, "The Unix_File object is intended to characterize Unix files.", "socket", 'string'),
        ("UNIX File", True, "Type", True, "The Unix_File object is intended to characterize Unix files.", "symboliclink", 'string'),
        ("UNIX File", True, "Type", True, "The Unix_File object is intended to characterize Unix files.", "blockspecialfile", 'string'),
        ("UNIX File", True, "Type", True, "The Unix_File object is intended to characterize Unix files.", "characterspecialfile", 'string'),
        ("UNIX Network Route Entry", False, None, False, "The Unix_Network_Route_Entry object is intended to characterize entries in the network routing table of a Unix system.", 'string'),
        ("UNIX Pipe", False, None, False, "The Unix_Pipe object is intended to characterize Unix pipes.", 'string'),
        ("UNIX Process", False, None, False, "The Unix_Process object is intended to characterize Unix processes.", 'string'),
        ("UNIX User Account", False, None, False, "The Unix_User_Account object is intended to characterize Unix user account objects.", 'string'),
        ("UNIX Volume", False, None, False, "The Unix_Volume object is intended to characterize Unix disk volumes.", 'string'),
        ("URI", True, "Type", True, "The URI object is intended to characterize Uniform Resource Identifiers (URI's).", "URL", 'string'),
        ("URI", True, "Type", True, "The URI object is intended to characterize Uniform Resource Identifiers (URI's).", "General URN", 'string'),
        ("URI", True, "Type", True, "The URI object is intended to characterize Uniform Resource Identifiers (URI's).", "Domain Name", 'string'),
        ("User Account", False, None, False, "The User_Account object is intended to characterize generic user accounts.", 'string'),
        ("User Session", False, None, False, "The User_Session object is intended to characterize user sessions.", 'string'),
        ("Volume", False, None, False, "The Volume object is intended to characterize generic drive volumes.", 'string'),
        ("Whois", False, None, False, "The Whois_Entry object is intended to characterize an individual Whois entry for a domain.", 'bigstring'),
        ("Win Computer Account", False, None, False, "The Windows_Computer_Account object is intended to characterize Windows computer accounts.", 'string'),
        ("Win Critical Section", False, None, False, "The Windows_Critical_Section object is intended to characterize Windows Critical Section objects.", 'string'),
        ("Win Driver", False, None, False, "The Windows_Driver object is intended to characterize Windows device drivers.", 'string'),
        ("Win Event Log", False, None, False, "The Windows_Event_Log object is intended to characterize entries in the Windows event log.", 'bigstring'),
        ("Win Event", False, None, False, "The Windows_Event object is intended to characterize Windows event (synchronization) objects.", 'string'),
        ("Win Executable File", False, None, False, "The Windows_Executable_File object is intended to characterize Windows PE (Portable Executable) files.", 'string'),
        ("Win File", False, None, False, "The Windows_File object is intended to characterize Windows files.", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "AccessToken", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "Event", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "File", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "FileMapping", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "Job", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "IOCompletion", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "Mailslot", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "Mutex", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "NamedPipe", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "Pipe", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "Process", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "Semaphore", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "Thread", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "Transaction", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "WaitableTimer", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "RegistryKey", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "Window", 'string'),
        ("Win Handle", True, "Type", True, "The Windows_Handle object is intended to characterize Windows handles.", "ServiceControl", 'string'),
        ("Win Kernel Hook", True, "Type", True, "The Windows_Kernel_Hook object is intended to characterize Windows kernel function hooks.", "IAT_API", 'string'),
        ("Win Kernel Hook", True, "Type", True, "The Windows_Kernel_Hook object is intended to characterize Windows kernel function hooks.", "Inline_Function", 'string'),
        ("Win Kernel Hook", True, "Type", True, "The Windows_Kernel_Hook object is intended to characterize Windows kernel function hooks.", "Instruction_Hooking", 'string'),
        ("Win Kernel", False, None, False, "The Windows_Kernel object is intended to characterize Windows Kernel structures.", 'string'),
        ("Win Mailslot", False, None, False, "The WindowsMailslotObjectType is intended to characterize Windows mailslot objects.", 'string'),
        ("Win Memory Page Region", False, None, False, "The Windows_Memory_Page_Region object is intended represent a single Windows memory page region.", 'string'),
        ("Win Mutex", False, None, False, "The WindowsMutexObject type is intended to characterize Windows mutual exclusion (mutex) objects.", 'string'),
        ("Win Network Route Entry", False, None, False, "The Windows_Network_Route_Entry object is intended to characterize Windows network routing table entries.", 'string'),
        ("Win Network Share", False, None, False, "The Windows_Network_Share object is intended to characterize Windows network shares.", 'string'),
        ("Win Pipe", False, None, False, "The Windows_Pipe object characterizes Windows pipes.", 'string'),
        ("Win Prefetch", False, None, False, "The Windows_Prefetch_Entry object is intended to characterize entries in the Windows prefetch files.", 'string'),
        ("Win Process", False, None, False, "The Windows_Process object is intended to characterize Windows processes.", 'string'),
        ("Win Registry Key", False, None, False, "The Windows_Registry_Key object characterizes windows registry objects, including Keys and Key/Value pairs.", 'string'),
        ("Win Semaphore", False, None, False, "The Windows_Semaphore object is intended to characterize Windows Semaphore (synchronization) objects.", 'string'),
        ("Win Service", False, None, False, "The Windows_Service object is intended to characterize Windows services.", 'string'),
        ("Win System", False, None, False, "The Windows_System object is intended to characterize Windows systems.", 'string'),
        ("Win System Restore", False, None, False, "The Windows_System_Restore_Entry object is intended to characterize Windows system restore points.", 'string'),
        ("Win Task", False, None, False, "The Windows_Task object is intended to characterize Windows task scheduler tasks.", 'string'),
        ("Win Thread", False, None, False, "The Windows_Thread object is intended to characterize Windows process threads.", 'string'),
        ("Win User Account", False, None, False, "The Windows_User_Account object is intended to characterize Windows user accounts.", 'string'),
        ("Win Volume", False, None, False, "The Windows_Volume object is intended to characterize Windows disk volumes.", 'string'),
        ("Win Waitable Timer", False, None, False, "The Windows_Waitable_Timer object is intended to characterize Windows waitable timer (synchronization) objects.", 'string'),
        ("X509 Certificate", False, None, False, "The X509_Certificate object is intended to characterize a public key certificate for use in a public key infrastructure.", 'bigstring')
    ]
    crits_types = [
        ("Base64 Alphabet", False, None, False, "The Base64 Alphabet object is intended to characterize a Base64 Alphabet.", 'bigstring'),
        ("DNS Calc Identifier", False, None, False, "The DNS Calc Identifier object is intended to characterize a DNS Calc Identifier.", 'string'),
        ("Win32 PE Debug Path", False, None, False, "The Win32 PE Debug Path object is intended to characterize a Win32 PE Debug Path.", 'string'),
        ("RC4 Key", False, None, False, "The RC4 Key object is intended to characterize an RC4 Key.", 'string'),
        ("Reference", False, None, False, "The Reference object is intended to characterize a Reference to related non-CRITs content.", 'bigstring'),
        ("C2 URL", False, None, False, "The C2 URL object is intended to characterize a C2 URL.", 'string'),
        ("PIVY Password", False, None, False, "The PIVY Password object is intended to characterize a PIVY Password.", 'string'),
        ("PIVY Group Name", False, None, False, "The PIVY Group Name object is intended to characterize a PIVY Group Name.", 'string'),
        ("Kill Chain", False, None, False, "The Kill Chain object is intended to characterize the different phases of the Kill Chain.", 'enum', ['Recon', 'Weaponize', 'Deliver', 'Exploit', 'Control', 'Execute', 'Maintain']),
        ("Document Metadata", False, None, False, "The Document Metadata object is intended to characterize Document Metadata.", 'bigstring')
    ]
    if not drop:
        print "Drop protection does not apply to object types"
    ObjectType.drop_collection()
    count = 0
    for t in types:
        ot = ObjectType()
        ot.active = 'off'
        ot.object_type = t[0]
        if not t[1]:
            ot.name = t[0]
            ot.is_subtype = False
            ot.name_type = None
            ot.description = t[4]
            if t[5] == 'enum':
                ot.datatype = {t[5]: t[6]}
            else:
                ot.datatype = {t[5]: 0}
        else:
            ot.name = t[5]
            ot.is_subtype = True
            ot.name_type = t[2]
            ot.description = t[4]
            if t[6] == 'enum':
                ot.datatype = {t[6]: t[7]}
            else:
                ot.datatype = {t[6]: 0}
        ot.version = "CybOX"
        ot.save()
        count += 1
    for t in crits_types:
        ot = ObjectType()
        ot.object_type = t[0]
        ot.name =  t[0]
        ot.is_subtype = False
        ot.name_type = None
        ot.description = t[4]
        ot.version = 'CRITs'
        if t[5] == 'enum':
            ot.datatype = {t[5]: t[6]}
        else:
            ot.datatype = {t[5]: 0}
        ot.save()
        count += 1
    print "Added %s Object Types." % count
