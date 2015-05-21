import logging

from mongoengine import Document
from mongoengine import StringField, IntField

from django.conf import settings

from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument

logger = logging.getLogger(__name__)

class Sector(CritsDocument, CritsSchemaDocument, Document):
    """
    CRITs Sector Class
    """

    meta = {
        "collection": settings.COL_SECTOR_LISTS,
        "crits_type": 'Sectorlist',
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'Sectorlist name',
            'Actor': 'Integer',
            'Backdoor': 'Integer',
            'Campaign': 'Integer',
            'Certificate': 'Integer',
            'Domain': 'Integer',
            'Email': 'Integer',
            'Event': 'Integer',
            'Exploit': 'Integer',
            'Target': 'Integer',
            'IP': 'Integer',
            'Indicator': 'Integer',
            'PCAP': 'Integer',
            'RawData': 'Integer',
            'Sample': 'Integer'
        },
    }

    name = StringField(required=True)
    Actor = IntField(default=0)
    Backdoor = IntField(default=0)
    Campaign = IntField(default=0)
    Certificate = IntField(default=0)
    Domain = IntField(default=0)
    Email = IntField(default=0)
    Event = IntField(default=0)
    Exploit = IntField(default=0)
    Indicator = IntField(default=0)
    IP = IntField(default=0)
    PCAP = IntField(default=0)
    RawData = IntField(default=0)
    Sample = IntField(default=0)
    Target = IntField(default=0)

    def migrate(self):
        """
        Migrate to the latest schema version.
        """

        pass


class SectorObject(CritsDocument, CritsSchemaDocument, Document):
    """
    Sector object class.
    """

    meta = {
        "crits_type": "SectorObject",
        "collection": settings.COL_SECTORS,
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'The name of the sector',
            'active': 'Enabled in the UI (on/off)',
        }
    }

    name = StringField()
    active = StringField(default="on")
