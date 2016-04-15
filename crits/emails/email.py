import datetime

from dateutil.parser import parse as date_parser
from mongoengine import Document, StringField, ListField
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsSourceDocument
from crits.core.crits_mongoengine import CritsActionsDocument
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


class Email(CritsBaseAttributes, CritsSourceDocument, CritsActionsDocument,
            Document):
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
