from crits.core.crits_mongoengine import EmbeddedObject
from cybox.objects.address_object import Address
from cybox.objects.email_message_object import EmailMessage
#from cybox.objects.mutex_object import Mutex
#from cybox.objects.registry_object import Registry_Key
from cybox.objects.uri_object import URI
#from cybox.objects.win_file_object import Win_File

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
    #TODO: Http Request Header Fields not implemented?
    #elif type_ == "Http Request Header Fields":
        #pass
    #TODO: Mutex object type is incomplete
    #elif type_ == "Mutex":
        #return Mutex.object_from_dict({'name': value})
    #TODO: use Byte_Run object?
    #elif type_ == "String":
       #pass
    elif type_ == "URI":
        #return URI(type_=name, value=value)
        r = URI()
        r.type_ = name
        r.value = value
        return r
    #TODO: Win_File incomplete
    #elif type_ == "Win File":
    #TODO: Registry_Key incomplete
    #elif type_ == "Win Handle" and name == "RegistryKey":
        #return Registry_Key.object_from_dict({'key':value})
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
    else:
        raise UnsupportedCRITsObjectTypeError(cybox_obj)
