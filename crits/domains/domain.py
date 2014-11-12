import datetime

from mongoengine import Document, StringField, ListField, EmbeddedDocumentField
from mongoengine import BooleanField, DynamicEmbeddedDocument, EmbeddedDocument
from difflib import unified_diff
from django.conf import settings
from whois_parser import WhoisEntry

from cybox.objects.domain_name_object import DomainName
from cybox.core import Observable

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsDocument
from crits.core.crits_mongoengine import CritsDocumentFormatter, CritsSourceDocument
from crits.core.crits_mongoengine import CommonAccess
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

class Domain(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    Domain Class.
    """

    meta = {
        "collection": settings.COL_DOMAINS,
        "crits_type": 'Domain',
        "latest_schema_version": 2,
        "schema_doc": {
            'analyst': 'Analyst who added/modified this domain',
            'domain': 'The domain name of this domain',
            'type': 'Record type of this domain',
            'watchlistEnabled': 'Boolean - whether this is a domain to watch',
            'whois': 'List [] of dictionaries of whois data on given dates',
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
    whois = ListField(EmbeddedDocumentField(EmbeddedWhoIs))
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

    def add_whois(self, data, analyst, date=None, editable=True):
        """
        Add whois information to the domain.

        :param data: The contents of the whois.
        :type data: str
        :param analyst: The user adding the whois.
        :type analyst: str
        :param date: The date for this whois entry.
        :type date: datetime.datetime
        :param editable: If this entry can be modified.
        :type editable: boolean
        :returns: :class:`crits.core.domains.domain.WhoisEntry`
        """

        if not date:
            date = datetime.datetime.now()
        whois_entry = WhoisEntry(data).to_dict()

        e = EmbeddedWhoIs()
        e.date = date
        e.analyst = analyst
        e.editable = editable
        e.text = data
        e.data = whois_entry
        self.whois.append(e)
        return whois_entry

    def edit_whois(self, data, date=None):
        """
        Edit whois information for the domain.

        :param data: The contents of the whois.
        :type data: str
        :param date: The date for this whois entry.
        :type date: datetime.datetime
        """

        if not date:
            return

        for w in self.whois:
            if w.date == date:
                whois_entry = WhoisEntry(data).to_dict()
                w.data = whois_entry
                w.text = data

    def delete_whois(self, date):
        """
        Remove whois information from the domain.

        :param date: The date for this whois entry.
        :type date: datetime.datetime
        """

        if not date:
            return

        for w in self.whois:
            if w.date == date:
                self.whois.remove(w)
                break

    def whois_diff(self, from_date, to_date):
        """
        Generate a diff between two whois entries.

        :param from_date: The date for the first whois entry.
        :type date: datetime.datetime
        :param to_date: The date for the second whois entry.
        :type date: datetime.datetime
        :returns: str, None
        """

        from_whois = None
        to_whois = None
        for w in self.whois:
            if w.date == from_date:
                from_whois = str(WhoisEntry.from_dict(w.data)).splitlines(True)
            if w.date == to_date:
                to_whois = str(WhoisEntry.from_dict(w.data)).splitlines(True)
        if not from_whois or not to_whois:
            return None
        return unified_diff(from_whois,
                            to_whois,
                            fromfile=from_date,
                            tofile=to_date)

    def to_cybox_observable(self):
        """
            Convert a Domain to a CybOX Observables.
            Returns a tuple of (CybOX object, releasability list).

            To get the cybox object as xml or json, call to_xml() or
            to_json(), respectively, on the resulting CybOX object.
        """
        obj = DomainName()
        obj.value = self.domain
        obj.type_ = self.record_type
        return ([Observable(obj)], self.releasability)

    @classmethod
    def from_cybox(cls, cybox_obs):
        """
        Convert a Cybox DefinedObject to a MongoEngine Domain object.

        :param cybox_obs: The cybox observable to create the Domain from.
        :type cybox_obs: :class:`cybox.core.Observable``
        :returns: :class:`crits.domains.domain.Domain`
        """
        cybox_object = cybox_obs.object_.properties
        db_obj = Domain.objects(domain=str(cybox_object.value)).first()
        if db_obj:
            return db_obj
        else:
            domain = cls()
            domain.domain = str(cybox_object.value)
            domain.record_type = str(cybox_object.type_)
            return domain


class DomainAccess(EmbeddedDocument, CritsDocumentFormatter, CommonAccess):
    """
    ACL for Domains.
    """

    whois_read = BooleanField(default=False)
    whois_add = BooleanField(default=False)
    whois_edit = BooleanField(default=False)
    whois_delete = BooleanField(default=False)
