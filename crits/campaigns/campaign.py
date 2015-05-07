import datetime

from mongoengine import Document, EmbeddedDocument, StringField, IntField
from mongoengine import EmbeddedDocumentField, DateTimeField, ListField
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsDocumentFormatter
from crits.campaigns.migrate import migrate_campaign


class EmbeddedTTP(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded TTP object
    """

    analyst = StringField(required=True)
    ttp = StringField(required=True)
    date = DateTimeField(default=datetime.datetime.now)

class Campaign(CritsBaseAttributes, Document):
    """
    Campaign Class.
    """

    meta = {
        "collection": settings.COL_CAMPAIGNS,
        "crits_type": 'Campaign',
        "latest_schema_version": 3,
        "schema_doc": {
            'schema_version': 'Version of the Campaign schema doc',
            'active': 'Enabled in the UI (on/off)',
            'aliases': 'List [] of aliases this Campaign goes by',
            'domain_count': 'Domains tagged with Campaign. Added by MapReduce',
            'email_count': 'Emails tagged with Campaign. Added by MapReduce',
            'event_count': 'Events tagged with Campaign. Added by MapReduce',
            'indicator_count': ('Indicators tagged with Campaign. Added by '
                                'MapReduce'),
            'ip_count': 'IPs tagged with Campaign. Added by MapReduce',
            'name': 'Name this Campaign goes by',
            'pcap_count': 'PCAPs tagged with Campaign. Added by MapReduce',
            'sample_count': 'Samples tagged with Campaign. Added by MapReduce',
            'ttps': 'List [] of TTPs this Campaign is associated with',
        },
        "jtable_opts": {
            'details_url': 'crits.campaigns.views.campaign_details',
            'details_url_key': 'name',
            'default_sort': "name ASC",
            'searchurl': 'crits.campaigns.views.campaigns_listing',
            'fields': ["name", "aliases", "actor_count", "backdoor_count",
                       "exploit_count", "indicator_count", "email_count",
                       "domain_count", "sample_count", "event_count",
                       "ip_count", "pcap_count", "modified", "id", "status"],
            'jtopts_fields': ["details", "name", "aliases", "status",
                              "actors", "backdoors", "exploits", "indicators",
                              "emails", "domains", "samples", "events", "ips",
                              "pcaps", "modified", "favorite", "id"],
            'hidden_fields': [],
            'linked_fields': [],
            'details_link': 'details',
            'no_sort': ['details']
        }
    }

    active = StringField(default="on")
    aliases = ListField(StringField(), default=[])
    actor_count = IntField(default=0)
    backdoor_count = IntField(default=0)
    domain_count = IntField(default=0)
    email_count = IntField(default=0)
    event_count = IntField(default=0)
    exploit_count = IntField(default=0)
    indicator_count = IntField(default=0)
    ip_count = IntField(default=0)
    name = StringField(default=0)
    pcap_count = IntField(default=0)
    sample_count = IntField(default=0)
    ttps = ListField(EmbeddedDocumentField(EmbeddedTTP), default=[])

    def migrate(self):
        """
        Migrate the Campaign to the latest schema version.
        """

        migrate_campaign(self)

    def activate(self):
        """
        Set the Campaign as active.
        """

        self.active = "on"

    def deactivate(self):
        """
        Set the Campaign as inactive.
        """

        self.active = "off"

    def edit_description(self, description):
        """
        Set the Campaign description.

        :param description: The campaign description.
        :type description: str

        """

        self.description = description

    def edit_name(self, name):
        """
        Change the Campaign name.

        :param name: The new campaign name.
        :type name: str

        """

        self.name = name

    def add_alias(self, alias):
        """
        Add a Campaign alias.

        :param alias: The campaign alias(es)
        :type alias: string or list of strings.

        """

        if isinstance(alias, basestring):
            alias = [alias]
        for a in alias:
            if a not in self.aliases and isinstance(a, basestring):
                self.aliases.append(a)

    def remove_alias(self, alias):
        """
        Remove a Campaign alias.

        :param alias: The alias to remove.
        :type alias: str

        """

        self.aliases.remove(alias)

    def set_aliases(self, aliases):
        """
        Set the Campaign aliases to a specified list.

        :param aliases: The alias to set.
        :type alias: list

        """

        if isinstance(aliases, list):
            self.aliases = aliases

    def get_aliases(self):
        """
        Get the list of Campaign aliases.

        :returns: list of aliases.

        """

        return [alias for alias in self._data['aliases']]

    def add_ttp(self, ttp_item):
        """
        Add a TTP to this Campaign.

        :param ttp_item: The TTP to add.
        :type ttp_item: EmbeddedTTP

        """

        if isinstance(ttp_item, EmbeddedTTP):
            found = False
            for ttp in self.ttps:
                if ttp.ttp == ttp_item.ttp:
                    found = True
            if not found:
                self.ttps.append(ttp_item)

    def edit_ttp(self, old_ttp=None, new_ttp=None):
        """
        Edit an existing TTP for this Campaign.

        :param old_ttp: The old TTP value.
        :type old_ttp: str
        :param new_ttp: The new TTP value.
        :type new_ttp: str

        """

        if old_ttp and new_ttp:
            for c, ttp in enumerate(self.ttps):
                if ttp.ttp == old_ttp:
                    self.ttps[c].ttp = new_ttp

    def remove_ttp(self, ttp_value=None):
        """
        Remove a TTP from this Campaign.

        :param ttp_value: The TTP value to remove.
        :type ttp_value: str

        """

        if ttp_value:
            for c, ttp in enumerate(self.ttps):
                if ttp_value == ttp.ttp:
                    del self.ttps[c]
