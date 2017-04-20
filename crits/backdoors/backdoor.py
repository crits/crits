from mongoengine import Document, StringField, ListField
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsSourceDocument
from crits.core.crits_mongoengine import CritsActionsDocument

class Backdoor(CritsBaseAttributes, CritsSourceDocument, CritsActionsDocument,
               Document):
    """
    Backdoor class.
    """

    meta = {
        "collection": settings.COL_BACKDOORS,
        "crits_type": 'Backdoor',
        "latest_schema_version": 1,
        "schema_doc": {
        },
        "jtable_opts": {
            'details_url': 'crits.backdoors.views.backdoor_detail',
            'details_url_key': 'id',
            'default_sort': "modified DESC",
            'searchurl': 'crits.backdoors.views.backdoors_listing',
            'fields': ["name", "version", "description", "modified", "source",
                       "campaign", "status", "id"],
            'jtopts_fields': ["details", "name", "version", "description",
                              "modified", "source", "campaign", "status",
                              "favorite", "id"],
            'hidden_fields': [],
            'linked_fields': ["source", "campaign"],
            'details_link': 'details',
            'no_sort': ['details'],
        }
    }

    name = StringField(required=True)
    aliases = ListField(StringField())
    version = StringField()

    def migrate(self):
        pass

    # XXX: Identical to Actor.update_aliases()
    def update_aliases(self, aliases):
        """
        Update the aliases on an Backdoor.

        :param aliases: The aliases we are setting.
        :type aliases: list
        """

        if isinstance(aliases, basestring):
            aliases = aliases.split(',')
        aliases = [a.strip() for a in aliases if a != '']
        existing_aliases = None
        if len(aliases) < len(self.aliases):
            self.aliases = aliases
        else:
            existing_aliases = self.aliases
        if existing_aliases is not None:
            for a in aliases:
                if a not in existing_aliases:
                    existing_aliases.append(a)
