from mongoengine import Document, StringField, IntField
from django.conf import settings

from crits.core.crits_mongoengine import (
    CritsSchemaDocument,
    CritsDocument
)


class Location(CritsDocument, CritsSchemaDocument, Document):
    """
    Location class.
    """

    meta = {
        "collection": settings.COL_LOCATIONS,
        "crits_type": 'Location',
        "latest_schema_version": 1,
        "schema_doc": {
            'active': 'Enabled in the UI (on/off)',
            'name': 'The name of this country',
            'country_code': 'The country code of this country',
            'iso2': 'The DAC iso2 value for this country',
            'iso3': 'The DAC iso3 value for this country',
            'region_code': 'The region code of this country',
            'region_name': 'The region name of this country',
        },
    }

    active = StringField(default="on")
    name = StringField(required=True)
    calling_code = IntField(required=False)
    cca2 = StringField(required=False)
    cca3 = StringField(required=False)
    ccn3 = StringField(required=False)
    cioc = StringField(required=False)
    region = StringField(required=True)
    sub_region = StringField(required=False)
    latitude = IntField(required=False)
    longitude = IntField(required=False)

    def migrate(self):
        pass
