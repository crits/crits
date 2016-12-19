import logging

from mongoengine import Document, EmbeddedDocument
from mongoengine import EmbeddedDocumentField
from mongoengine import StringField, ListField, BooleanField

from django.conf import settings

from crits.actors.actor import ActorAccess, ActorIdentifierAccess
from crits.backdoors.backdoor import BackdoorAccess
from crits.campaigns.campaign import CampaignAccess
from crits.certificates.certificate import CertificateAccess
from crits.domains.domain import DomainAccess
from crits.emails.email import EmailAccess
from crits.events.event import EventAccess
from crits.exploits.exploit import ExploitAccess
from crits.indicators.indicator import IndicatorAccess
from crits.ips.ip import IPAccess
from crits.pcaps.pcap import PCAPAccess
from crits.raw_data.raw_data import RawDataAccess
from crits.samples.sample import SampleAccess
from crits.targets.target import TargetAccess
from crits.signatures.signature import SignatureAccess
from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument
from crits.core.crits_mongoengine import CritsDocumentFormatter
from crits.core.source_access import SourceAccess

logger = logging.getLogger(__name__)

class EmbeddedSourceACL(EmbeddedDocument, CritsDocumentFormatter):
    """
    Source ACL.
    """

    name = StringField(required=True)
    read = BooleanField(default=False)
    write = BooleanField(default=False)
    tlp_red = BooleanField(default=False)
    tlp_amber = BooleanField(default=False)
    tlp_green = BooleanField(default=False)

class Role(CritsDocument, CritsSchemaDocument, Document):
    """
    CRITs Role Class
    """

    meta = {
        "collection": settings.COL_ROLES,
        "crits_type": 'Role',
        "latest_schema_version": 1,
        "schema_doc": {
        },
        "jtable_opts": {
                         'details_url': 'crits.core.views.role_details',
                         'details_url_key': 'id',
                         'default_sort': "name ASC",
                         'searchurl': 'crits.core.views.roles_listing',
                          'fields': [ "name", "active", "description",
                                      "id" ],
                          'jtopts_fields': [ "details",
                                             "name",
                                             "active",
                                             "description" ],
                         'hidden_fields': [],
                         'linked_fields': [],
                         'details_link': 'details',
                         'no_sort': ['details']
                       }
    }

    name = StringField(required=True)
    active = StringField(default="on")
    description = StringField()
    sources = ListField(EmbeddedDocumentField(EmbeddedSourceACL))

    # TLOs
    Actor = EmbeddedDocumentField(ActorAccess, required=True,
                                  default=ActorAccess())
    ActorIdentifier = EmbeddedDocumentField(ActorIdentifierAccess,
                                            required=True,
                                            default=ActorIdentifierAccess())
    Backdoor = EmbeddedDocumentField(BackdoorAccess, required=True,
                                     default=BackdoorAccess())
    Campaign = EmbeddedDocumentField(CampaignAccess, required=True,
                                     default=CampaignAccess())
    Certificate = EmbeddedDocumentField(CertificateAccess, required=True,
                                        default=CertificateAccess())
    Domain = EmbeddedDocumentField(DomainAccess, required=True,
                                   default=DomainAccess())
    Email = EmbeddedDocumentField(EmailAccess, required=True,
                                  default=EmailAccess())
    Event = EmbeddedDocumentField(EventAccess, required=True,
                                  default=EventAccess())
    Exploit = EmbeddedDocumentField(ExploitAccess, required=True,
                                  default=ExploitAccess())
    Indicator = EmbeddedDocumentField(IndicatorAccess, required=True,
                                      default=IndicatorAccess())
    IP = EmbeddedDocumentField(IPAccess, required=True,
                               default=IPAccess())
    PCAP = EmbeddedDocumentField(PCAPAccess, required=True,
                                 default=PCAPAccess())
    RawData = EmbeddedDocumentField(RawDataAccess, required=True,
                                    default=RawDataAccess())
    Sample = EmbeddedDocumentField(SampleAccess, required=True,
                                   default=SampleAccess())
    Signature = EmbeddedDocumentField(SignatureAccess, required=True,
                                      default=SignatureAccess())
    Target = EmbeddedDocumentField(TargetAccess, required=True,
                                   default=TargetAccess())

    # Interfacing
    api_interface = BooleanField(default=False)
    script_interface = BooleanField(default=False)
    web_interface = BooleanField(default=False)

    # Add New
    add_new_actor_identifier_type = BooleanField(default=False)
    add_new_indicator_action = BooleanField(default=False)
    add_new_raw_data_type = BooleanField(default=False)
    add_new_signature_dependency = BooleanField(default=False)
    add_new_signature_type = BooleanField(default=False)
    add_new_source = BooleanField(default=False)
    add_new_user_role = BooleanField(default=False)
    add_new_tlds = BooleanField(default=False)

    # Control Panel
    control_panel_read = BooleanField(default=False)
    control_panel_system_read = BooleanField(default=False)
    control_panel_general_read = BooleanField(default=False)
    control_panel_general_edit = BooleanField(default=False)
    control_panel_crits_read = BooleanField(default=False)
    control_panel_crits_edit = BooleanField(default=False)
    control_panel_ldap_read = BooleanField(default=False)
    control_panel_ldap_edit = BooleanField(default=False)
    control_panel_security_read = BooleanField(default=False)
    control_panel_security_edit = BooleanField(default=False)
    control_panel_downloading_read = BooleanField(default=False)
    control_panel_downloading_edit = BooleanField(default=False)
    control_panel_system_services_read = BooleanField(default=False)
    control_panel_system_services_edit = BooleanField(default=False)
    control_panel_logging_read = BooleanField(default=False)
    control_panel_logging_edit = BooleanField(default=False)
    control_panel_items_read = BooleanField(default=False)
    control_panel_users_read = BooleanField(default=False)
    control_panel_users_add = BooleanField(default=False)
    control_panel_users_edit = BooleanField(default=False)
    control_panel_users_active = BooleanField(default=False)
    control_panel_roles_read = BooleanField(default=False)
    control_panel_roles_edit = BooleanField(default=False)
    control_panel_services_read = BooleanField(default=False)
    control_panel_services_edit = BooleanField(default=False)
    control_panel_audit_log_read = BooleanField(default=False)

    # Recent Activity
    recent_activity_read = BooleanField(default=False)

    # Structured Exchange Formats
    stix_import_add = BooleanField(default=False)

    # Timelines
    dns_timeline_read = BooleanField(default=False)
    emails_timeline_read = BooleanField(default=False)
    indicators_timeline_read = BooleanField(default=False)


    def migrate(self):
        """
        Migrate to the latest schema version.
        """

        pass

    def make_all_true(self):
        """
        Makes all ACL options True
        """

        dont_modify = ['name',
                       'schema_version',
                       'active',
                       'id',
                       'description',
                       'unsupported_attrs']

        for p in self._data.iterkeys():
            if p in settings.CRITS_TYPES.iterkeys():
                attr = getattr(self, p)
                # Modify the attributes.
                for x in attr._data.iterkeys():
                    setattr(attr, x, True)
                # Set the attribute on the ACL.
                setattr(self, p, attr)
            elif p == "sources":
                for s in getattr(self, p):
                    for x in s._data.iterkeys():
                        if x != "name":
                            setattr(s, x, True)
            elif p not in dont_modify:
                setattr(self, p, True)

    def add_all_sources(self):
        """
        Add all of the sources to this Role
        """

        sources = SourceAccess.objects()
        for s in sources:
            self.add_source(s.name,read=True,write=True,tlp_red=True,tlp_amber=True,tlp_green=True)

    def add_source(self, source, read=False, write=False,
                   tlp_red=False, tlp_amber=False, tlp_green=False):
        """
        Add a source to this Role.

        :param source: The name of the source.
        :type source: str
        """

        found = False
        for s in self.sources:
            if s.name == source:
                found = True
                break
        if not found:
            src = SourceAccess.objects(name=source).first()
            if src:
                new_src = EmbeddedSourceACL(name=source,
                                            read=read,
                                            write=write,
                                            tlp_red=tlp_red,
                                            tlp_amber=tlp_amber,
                                            tlp_green=tlp_green)
                self.sources.append(new_src)
