from mongoengine import Document, StringField
from mongoengine import BooleanField, DynamicEmbeddedDocument
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsDocument
from crits.core.crits_mongoengine import CritsDocumentFormatter, CritsSourceDocument
from crits.core.crits_mongoengine import CritsActionsDocument
from crits.domains.migrate import migrate_domain

class TLD(CritsDocument, Document):
    """
    TLD class for adding TLDs to the database.
    """

    meta = {
        "collection": settings.COL_EFFECTIVE_TLDS,
        "crits_type": 'TLD',
        "latest_schema_version": 1,
        "schema_doc": {
            'tld': 'The domain TLD',
        },
    }

    tld = StringField(required=True)

class EmbeddedWhoIs(DynamicEmbeddedDocument, CritsDocumentFormatter):
    """
    EmbeddedWhoIs Class.
    """

    meta = {
        'allow_inheritance': False
    }

class Domain(CritsBaseAttributes, CritsSourceDocument, CritsActionsDocument,
             Document):
    """
    Domain Class.
    """

    meta = {
        "collection": settings.COL_DOMAINS,
        "crits_type": 'Domain',
        "latest_schema_version": 3,
        "schema_doc": {
            'analyst': 'Analyst who added/modified this domain',
            'domain': 'The domain name of this domain',
            'type': 'Record type of this domain',
            'watchlistEnabled': 'Boolean - whether this is a domain to watch',
        },
        "jtable_opts": {
                         'details_url': 'crits.domains.views.domain_detail',
                         'details_url_key': 'domain',
                         'default_sort': "domain ASC",
                         'searchurl': 'crits.domains.views.domains_listing',
                         'fields': [ "domain", "modified", "source",
                                     "campaign", "status", "id"],
                         'jtopts_fields': [ "details",
                                            "domain",
                                            "modified",
                                            "source",
                                            "campaign",
                                            "status",
                                            "favorite",
                                            "id"],
                         'hidden_fields': [],
                         'linked_fields': ["source", "campaign"],
                         'details_link': 'details',
                         'no_sort': ['details']
                       }

    }

    domain = StringField(required=True)
    record_type = StringField(default="A", db_field="type")
    watchlistEnabled = BooleanField(default=False)
    analyst = StringField()

    def migrate(self):
        """
        Migrate to the latest schema version.
        """

        migrate_domain(self)

    def _custom_save(self, force_insert=False, validate=True, clean=False,
        write_concern=None, cascade=None, cascade_kwargs=None,
        _refs=None, username=None, **kwargs):
        """
        Custom save. Overrides default core custom save function.
        """

        #TODO: parse for potential root domain and add it as well?
        # - would require adding relationships between the two as well
        return super(self.__class__, self)._custom_save(force_insert, validate,
            clean, write_concern, cascade, cascade_kwargs, _refs, username)
