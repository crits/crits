from mongoengine import Document, StringField
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsSourceDocument, CritsActionsDocument
from crits.ips.migrate import migrate_ip


class IP(CritsBaseAttributes, CritsActionsDocument, CritsSourceDocument, Document):
    """
    IP class.
    """

    meta = {
        "collection": settings.COL_IPS,
        "crits_type": 'IP',
        "latest_schema_version": 3,
        "schema_doc": {
            'ip': 'The IP address',
            'type': ('The type of IP address.'
                    ' Object Types'),
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

    def migrate(self):
        migrate_ip(self)
