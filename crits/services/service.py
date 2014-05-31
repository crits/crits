from mongoengine import Document, StringField, ListField
from mongoengine import BooleanField, EmbeddedDocumentField
from django.conf import settings

from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument
from crits.core.crits_mongoengine import AnalysisConfig


class CRITsService(CritsDocument, CritsSchemaDocument, Document):
    """
    CRITs Service class.
    """

    meta = {
        "crits_type": "Service",
        "collection": settings.COL_SERVICES,
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'Name of the service',
            'config': 'Dicionary of configuration items',
            'description': 'Description of the service',
            'enabled': 'If this service is enabled',
            'purpose': 'What this service is used for',
            'required_fields': 'Config fields required for service to run',
            'rerunnable': 'If this service can be run more than once',
            'run_on_triage': 'If this service runs on upload',
            'service_type': 'The type of service this is',
            'status': 'The status of this service',
            'supported_types': 'CRITs types this service supports',
            'version': 'Version string of this service',
        }
    }

    name = StringField(required=True)
    config = EmbeddedDocumentField(AnalysisConfig)
    description = StringField()
    enabled = BooleanField()
    purpose = StringField()
    required_fields = ListField(StringField())
    rerunnable = BooleanField()
    run_on_triage = BooleanField()
    service_type = StringField(db_field='type')
    status = StringField()
    supported_types = ListField(StringField())
    version = StringField()
