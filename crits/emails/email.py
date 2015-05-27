import datetime

from dateutil.parser import parse as date_parser
from mongoengine import Document, StringField, ListField
from django.conf import settings
from cybox.common import String, DateTime
from cybox.core import Observable
from cybox.objects.address_object import Address, EmailAddress
from cybox.objects.email_message_object import EmailHeader, EmailMessage, Attachments

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsSourceDocument
from crits.core.fields import CritsDateTimeField
from crits.emails.migrate import migrate_email

from crits.core.data_tools import convert_datetimes_to_string

class RawHeadersField(StringField):
    """
    Raw Header class.
    """

    def transform(self, value):
        """
        If we receive a list instead of a string, convert it.

        :param value: The raw headers.
        :type value: str or list
        :returns: str
        """

        if isinstance(value, list):
            tmp = ''
            for v in value:
                tmp = ' '.join([tmp, self.transform(v)])
            return tmp
        return value


class Email(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    Email Class.
    """

    meta = {
        # mongoengine adds fields _cls and _types and uses them to filter database
        # responses unless you disallow inheritance. In other words, we
        # can't see any of our old data unless we add _cls and _types
        # attributes to them or turn off inheritance.
        #So we'll turn inheritance off.
        # (See http://mongoengine-odm.readthedocs.org/en/latest/guide/defining-documents.html#working-with-existing-data)
        "collection": settings.COL_EMAIL,
        "crits_type": 'Email',
        "latest_schema_version": 2,
        "schema_doc": {
            'boundary': 'Email boundary',
            'campaign': 'List [] of campaigns attributed to this email',
            'cc': 'List [] of CC recipients',
            'date': 'String of date header field',
            'from': 'From header field',
            'helo': 'HELO',
            'isodate': 'ISODate conversion of date header field',
            'message_id': 'Message-ID header field',
            'modified': 'When this object was last modified',
            'objects': 'List of objects in this email',
            'originating_ip': 'Originating-IP header field',
            'raw_body': 'Email raw body',
            'raw_header': 'Email raw headers',
            'relationships': 'List of relationships with this email',
            'reply_to': 'Reply-To header field',
            'sender': 'Sender header field',
            'shared_with': 'Dictionary of sources that this email may be shared with and whether it has been shared already',
            'source': 'List [] of sources that provided information on this email',
            'subject': 'Email subject',
            'to': 'To header field',
            'x_originating_ip': 'X-Originating-IP header field',
            'x_mailer': 'X-Mailer header field',
        },
        "jtable_opts": {
                         'details_url': 'crits.emails.views.email_detail',
                         'details_url_key': 'id',
                         'default_sort': "isodate DESC",
                         'searchurl': 'crits.emails.views.emails_listing',
                         'fields': [ "from_address", "subject", "isodate",
                                     "source", "campaign", "id", "to",
                                     "status", "cc" ],
                          'jtopts_fields': [ "details",
                                             "from",
                                             "recip",
                                             "subject",
                                             "isodate",
                                             "source",
                                             "campaign",
                                             "status",
                                             "favorite",
                                             "id"],
                         'hidden_fields': [],
                         'linked_fields': [ "source", "campaign",
                                            "from", "subject" ],
                         'details_link': 'details',
                         'no_sort': ['recip', 'details']
                       }
    }

    boundary = StringField()
    cc = ListField(StringField())
    date = StringField(required=True)
    from_address = StringField(db_field="from")
    helo = StringField()
    # isodate is an interally-set attribute and on save will be overwritten
    # with the isodate version of the email's date attribute.
    isodate = CritsDateTimeField()
    message_id = StringField()
    originating_ip = StringField()
    raw_body = StringField()
    raw_header = RawHeadersField(db_field="raw_headers")
    reply_to = StringField()
    sender = StringField()
    subject = StringField()
    to = ListField(StringField())
    x_originating_ip = StringField()
    x_mailer = StringField()

    def migrate(self):
        """
        Migrate to latest schema version.
        """

        migrate_email(self)

    def _custom_save(self, force_insert=False, validate=True, clean=False,
        write_concern=None,  cascade=None, cascade_kwargs=None,
        _refs=None, username=None, **kwargs):
        """
        Override our core custom save. This will ensure if there is a "date"
        string available for the email that we generate a corresponding
        "isodate" field which is more useful for database sorting/searching.
        """

        if hasattr(self, 'date'):
            if self.date:
                if isinstance(self.date, datetime.datetime):
                    self.isodate = self.date
                    self.date = convert_datetimes_to_string(self.date)
                else:
                    self.isodate = date_parser(self.date, fuzzy=True)
            else:
                if self.isodate:
                    if isinstance(self.isodate, datetime.datetime):
                        self.date = convert_datetimes_to_string(self.isodate)
        else:
            self.isodate = None

        return super(self.__class__, self)._custom_save(force_insert, validate,
            clean, write_concern, cascade, cascade_kwargs, _refs, username)

    def to_cybox_observable(self, exclude=None):
        """
        Convert an email to a CybOX Observables.

        Pass parameter exclude to specify fields that should not be
        included in the returned object.

        Returns a tuple of (CybOX object, releasability list).

        To get the cybox object as xml or json, call to_xml() or
        to_json(), respectively, on the resulting CybOX object.
        """

        if exclude == None:
            exclude = []

        observables = []

        obj = EmailMessage()
        # Assume there is going to be at least one header
        obj.header = EmailHeader()

        if 'message_id' not in exclude:
            obj.header.message_id = String(self.message_id)

        if 'subject' not in exclude:
            obj.header.subject = String(self.subject)

        if 'sender' not in exclude:
            obj.header.sender = Address(self.sender, Address.CAT_EMAIL)

        if 'reply_to' not in exclude:
            obj.header.reply_to = Address(self.reply_to, Address.CAT_EMAIL)

        if 'x_originating_ip' not in exclude:
            obj.header.x_originating_ip = Address(self.x_originating_ip,
                                                  Address.CAT_IPV4)

        if 'x_mailer' not in exclude:
            obj.header.x_mailer = String(self.x_mailer)

        if 'boundary' not in exclude:
            obj.header.boundary = String(self.boundary)

        if 'raw_body' not in exclude:
            obj.raw_body = self.raw_body

        if 'raw_header' not in exclude:
            obj.raw_header = self.raw_header

        #copy fields where the names differ between objects
        if 'helo' not in exclude and 'email_server' not in exclude:
            obj.email_server = String(self.helo)
        if ('from_' not in exclude and 'from' not in exclude and
            'from_address' not in exclude):
            obj.header.from_ = EmailAddress(self.from_address)
        if 'date' not in exclude and 'isodate' not in exclude:
            obj.header.date = DateTime(self.isodate)

	obj.attachments = Attachments()

        observables.append(Observable(obj))
        return (observables, self.releasability)

    @classmethod
    def from_cybox(cls, cybox_obs):
        """
        Convert a Cybox DefinedObject to a MongoEngine Email object.

        :param cybox_obs: The cybox object to create the Email from.
        :type cybox_obs: :class:`cybox.core.Observable``
        :returns: :class:`crits.emails.email.Email`
        """

        cybox_obj = cybox_obs.object_.properties
        email = cls()

        if cybox_obj.header:
            email.from_address = str(cybox_obj.header.from_)
            if cybox_obj.header.to:
                email.to = [str(recpt) for recpt in cybox_obj.header.to.to_list()]
            for field in ['message_id', 'sender', 'reply_to', 'x_originating_ip',
                          'subject', 'date', 'x_mailer', 'boundary']:
                setattr(email, field, str(getattr(cybox_obj.header, field)))

        email.helo = str(cybox_obj.email_server)
        if cybox_obj.raw_body:
            email.raw_body = str(cybox_obj.raw_body)
        if cybox_obj.raw_header:
            email.raw_header = str(cybox_obj.raw_header)

        return email
