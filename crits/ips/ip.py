from mongoengine import Document, StringField, ListField, DictField
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsSourceDocument
from crits.ips.migrate import migrate_ip

from cybox.objects.address_object import Address
from cybox.core import Observable

class IP(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    IP class.
    """

    meta = {
        "collection": settings.COL_IPS,
        "crits_type": 'IP',
        "latest_schema_version": 1,
        "schema_doc": {
            'ip': 'The IP address',
            'type': ('The type of IP address based on a subset of CybOX Address'
                    ' Object Types'),
            'whois': 'List [] of dictionaries of whois data on given dates',
        },
        "jtable_opts": {
                         'details_url': 'crits.ips.views.ip_detail',
                         'details_url_key': 'ip',
                         'default_sort': "modified DESC",
                         'searchurl': 'crits.ips.views.ips_listing',
                         'fields': [ "ip", "ip_type", "created", "modified",
                                     "source", "campaign", "status", "id"],
                         'jtopts_fields': [ "details",
                                            "ip",
                                            "type",
                                            "created",
                                            "modified",
                                            "source",
                                            "campaign",
                                            "status",
                                            "favorite",
                                            "id"],
                         'hidden_fields': [],
                         'linked_fields': ["ip", "source", "campaign", "type"],
                         'details_link': 'details',
                         'no_sort': ['details']
                       }

    }

    ip = StringField(required=True)
    ip_type = StringField(default="Address - ipv4-addr", db_field="type")
    whois = ListField(DictField)

    def migrate(self):
        migrate_ip(self)

    def to_cybox_observable(self):
        """
            Convert an IP to a CybOX Observables.
            Returns a tuple of (CybOX object, releasability list).

            To get the cybox object as xml or json, call to_xml() or
            to_json(), respectively, on the resulting CybOX object.
        """
        obj = Address()
	obj.address_value = self.ip

	temp_type = self.ip_type.replace("-", "")
	if temp_type.find(Address.CAT_ASN.replace("-", "")) >= 0:
	    obj.category = Address.CAT_ASN
	elif temp_type.find(Address.CAT_ATM.replace("-", "")) >= 0:
	    obj.category = Address.CAT_ATM
	elif temp_type.find(Address.CAT_CIDR.replace("-", "")) >= 0:
	    obj.category = Address.CAT_CIDR
	elif temp_type.find(Address.CAT_MAC.replace("-", "")) >= 0:
	    obj.category = Address.CAT_MAC
	elif temp_type.find(Address.CAT_IPV4.replace("-", "")) >= 0:
	    obj.category = Address.CAT_IPV4
	elif temp_type.find(Address.CAT_IPV4_NET.replace("-", "")) >= 0:
	    obj.category = Address.CAT_IPV4_NET
	elif temp_type.find(Address.CAT_IPV4_NETMASK.replace("-", "")) >= 0:
	    obj.category = Address.CAT_IPV4_NETMASK
	elif temp_type.find(Address.CAT_IPV6.replace("-", "")) >= 0:
	    obj.category = Address.CAT_IPV6
	elif temp_type.find(Address.CAT_IPV6_NET.replace("-", "")) >= 0:
	    obj.category = Address.CAT_IPV6_NET
	elif temp_type.find(Address.CAT_IPV6_NETMASK.replace("-", "")) >= 0:
	    obj.category = Address.CAT_IPV6_NETMASK

        return ([Observable(obj)], self.releasability)

    def stix_description(self):
        return "Category: %s" % self.ip_type

    def stix_intent(self):
        return "Observations"

    def stix_title(self):
        return self.ip
