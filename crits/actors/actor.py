import datetime

from mongoengine import Document, EmbeddedDocument, StringField, ListField
from mongoengine import EmbeddedDocumentField
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsSourceDocument
from crits.core.crits_mongoengine import CritsDocumentFormatter
from crits.core.crits_mongoengine import CritsSchemaDocument, CritsDocument
from crits.core.fields import CritsDateTimeField

class ActorThreatType(CritsDocument, CritsSchemaDocument, Document):
    """
    Actor Threat Type class.
    """

    meta = {
        "crits_type": "ActorThreatType",
        "collection": settings.COL_ACTOR_THREAT_TYPES,
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'Name of the Threat Type',
            'active': 'Enabled in the UI (on/off)',
        }
    }

    name = StringField()
    active = StringField(default="on")


class ActorMotivation(CritsDocument, CritsSchemaDocument, Document):
    """
    Actor Motivation class.
    """

    meta = {
        "crits_type": "ActorMotivation",
        "collection": settings.COL_ACTOR_MOTIVATIONS,
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'Name of the Motivation',
            'active': 'Enabled in the UI (on/off)',
        }
    }

    name = StringField()
    active = StringField(default="on")


class ActorSophistication(CritsDocument, CritsSchemaDocument, Document):
    """
    Actor Sophistication class.
    """

    meta = {
        "crits_type": "ActorSophistication",
        "collection": settings.COL_ACTOR_SOPHISTICATIONS,
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'Name of the Sophistication',
            'active': 'Enabled in the UI (on/off)',
        }
    }

    name = StringField()
    active = StringField(default="on")


class ActorIntendedEffect(CritsDocument, CritsSchemaDocument, Document):
    """
    Actor Intended Effect class.
    """

    meta = {
        "crits_type": "ActorIntendedEffect",
        "collection": settings.COL_ACTOR_INTENDED_EFFECTS,
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'Name of the Intended Effect',
            'active': 'Enabled in the UI (on/off)',
        }
    }

    name = StringField()
    active = StringField(default="on")


class ActorThreatIdentifier(CritsDocument, CritsSchemaDocument, Document):
    """
    Actor Threat Identifier class.
    """

    meta = {
        "crits_type": "ActorThreatIdentifier",
        "collection": settings.COL_ACTOR_THREAT_IDENTIFIERS,
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'Name of the Idenfifier',
            'active': 'Enabled in the UI (on/off)',
        }
    }

    name = StringField()
    active = StringField(default="on")


class EmbeddedActorIdentifier(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Actor Identifier class.
    """

    analyst = StringField(required=True)
    date = CritsDateTimeField(default=datetime.datetime.now)
    identifier_id = StringField(required=True)
    confidence = StringField(default="unknown")


class ActorIdentifier(CritsDocument, CritsSchemaDocument, CritsSourceDocument,
                      Document):
    """
    Actor Identifier class.
    """

    meta = {
        "collection": settings.COL_ACTOR_IDENTIFIERS,
        "crits_type": 'ActorIdentifier',
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'The name of this Action',
            'active': 'Enabled in the UI (on/off)'
        },
        "jtable_opts": {
                         'details_url': '',
                         'details_url_key': '',
                         'default_sort': "date DESC",
                         'searchurl': 'crits.actors.views.actor_identifiers_listing',
                         'fields': [ "name", "created", "source",
                                    "identifier_type", "id"],
                         'jtopts_fields': [ "name",
                                            "identifier_type",
                                            "created",
                                            "source",
                                            "favorite",
                                            "id"],
                         'hidden_fields': [],
                         'linked_fields': ["source"],
                         'details_link': '',
                         'no_sort': ['']
                       }
    }

    active = StringField(default="on")
    created = CritsDateTimeField(default=datetime.datetime.now)
    identifier_type = StringField(required=True)
    name = StringField(required=True)


class Actor(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    Actor class.
    """

    meta = {
        "collection": settings.COL_ACTORS,
        "crits_type": 'Actor',
        "latest_schema_version": 1,
        "schema_doc": {
        },
        "jtable_opts": {
                         'details_url': 'crits.actors.views.actor_detail',
                         'details_url_key': 'id',
                         'default_sort': "modified DESC",
                         'searchurl': 'crits.actors.views.actors_listing',
                         'fields': [ "name", "description", "modified",
                                     "source", "campaign", "status", "id"],
                         'jtopts_fields': [ "details",
                                            "name",
                                            "description",
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

    name = StringField(required=True)
    aliases = ListField(StringField())
    description = StringField()
    identifiers = ListField(EmbeddedDocumentField(EmbeddedActorIdentifier))
    intended_effects = ListField(StringField())
    motivations = ListField(StringField())
    sophistications = ListField(StringField())
    threat_types = ListField(StringField())

    def migrate(self):
        pass
