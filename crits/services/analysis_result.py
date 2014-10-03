from django.conf import settings
from mongoengine import Document, StringField, ListField, EmbeddedDocument
from mongoengine import DynamicEmbeddedDocument, DynamicField, UUIDField
from mongoengine import DictField, EmbeddedDocumentField, BooleanField

from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument
from crits.core.crits_mongoengine import CritsDocumentFormatter

# Embedded Documents common to most classes

class AnalysisConfig(DynamicEmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Analysis Configuration dictionary.
    """

    meta = {}


class EmbeddedAnalysisResultLog(EmbeddedDocument, CritsDocumentFormatter):
    """
    Log entry for a service run.
    """

    message = StringField()
    #TODO: this should be a datetime object
    datetime = StringField()
    level = StringField()


class AnalysisResult(CritsDocument, CritsSchemaDocument, CritsDocumentFormatter,
                     Document):
    """
    Analysis Result from running an analytic service.
    """

    meta = {
        "crits_type": "AnalysisResult",
        "collection": settings.COL_ANALYSIS_RESULTS,
        "latest_schema_version": 1,
        "schema_doc": {
            'analyst': 'Analyst who ran the service.',
            'analysis_id': 'Unique ID for this service execution.',
            'analysis_type': 'Type of analysis this is.',
            'config': 'Configuration options used for this execution.',
            'distributed': 'Distributed for this execution.',
            'finish_date': 'Date execution finished.',
            'log': 'Log entries for this execution.',
            'object_type': 'Type of TLO this is for.',
            'object_id': 'ObjectId of the TLO.',
            'results': 'Analysis results.',
            'service_name': 'Name of the service.',
            'source': 'Source of the service.',
            'start_date': 'Date execution started.',
            'status': 'Status of the execution.',
            'template': 'Custom template to render results.',
            'version': 'Version of the service used.',
        },
        "jtable_opts": {
                         'details_url': 'crits.services.views.analysis_result',
                         'details_url_key': 'id',
                         'default_sort': "start_date DESC",
                         'searchurl': 'crits.services.views.analysis_results_listing',
                         'fields': [ "object_type", "service_name", "version",
                                     "start_date", "finish_date", "results",
                                     "object_id", "id"],
                         'jtopts_fields': [ "details",
                                            "object_type",
                                            "service_name",
                                            "version",
                                            "start_date",
                                            "finish_date",
                                            "results",
                                            "id"],
                         'hidden_fields': ["object_id", "id"],
                         'linked_fields': [ "object_type", "service_name" ],
                         'details_link': 'details',
                         'no_sort': ['details']
                       }
    }

    #TODO: these should be datetime objects, not strings
    analyst = StringField()
    analysis_id = UUIDField(binary=False)
    analysis_type = StringField(db_field="type")
    config = EmbeddedDocumentField(AnalysisConfig)
    distributed = BooleanField()
    finish_date = StringField()
    log = ListField(EmbeddedDocumentField(EmbeddedAnalysisResultLog))
    object_type = StringField(required=True)
    object_id = StringField(required=True)
    results = ListField(DynamicField(DictField))
    service_name = StringField()
    source = StringField()
    start_date = StringField()
    status = StringField()
    template = StringField()
    version = StringField()
