import datetime

from mongoengine import Document, EmbeddedDocument, StringField, ListField
from mongoengine import EmbeddedDocumentField
from django.conf import settings

from crits.actors.migrate import migrate_actor
from crits.core.crits_mongoengine import CritsBaseAttributes, CritsSourceDocument
from crits.core.crits_mongoengine import CritsDocumentFormatter
from crits.core.crits_mongoengine import CritsSchemaDocument, CritsDocument
from crits.core.fields import CritsDateTimeField
from crits.core.user_tools import user_sources

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
            'default_sort': "created DESC",
            'searchurl': 'crits.actors.views.actor_identifiers_listing',
            'fields': ["name", "created", "source", "identifier_type", "id"],
            'jtopts_fields': ["name", "identifier_type", "created", "source"],
            'hidden_fields': [],
            'linked_fields': ["name", "source"],
            'details_link': '',
            'no_sort': [''],
        }
    }

    active = StringField(default="on")
    created = CritsDateTimeField(default=datetime.datetime.now)
    identifier_type = StringField(required=True)
    # name is misleading, it's actually the value. We use name so we can
    # leverage a lot of the work done for Item editing in the control panel and
    # changing active state.
    name = StringField(required=True)

    def set_identifier_type(self, identifier_type):
        identifier_type = identifier_type.strip()
        it = ActorThreatIdentifier.objects(name=identifier_type).first()
        if it:
            self.identifier_type = identifier_type

class Actor(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    Actor class.
    """

    meta = {
        "collection": settings.COL_ACTORS,
        "crits_type": 'Actor',
        "latest_schema_version": 2,
        "schema_doc": {
        },
        "jtable_opts": {
            'details_url': 'crits.actors.views.actor_detail',
            'details_url_key': 'id',
            'default_sort': "modified DESC",
            'searchurl': 'crits.actors.views.actors_listing',
            'fields': ["name", "description", "modified", "source", "campaign",
                       "status", "id"],
            'jtopts_fields': ["details", "name", "description", "modified",
                              "source", "campaign", "status", "favorite", "id"],
            'hidden_fields': [],
            'linked_fields': ["source", "campaign"],
            'details_link': 'details',
            'no_sort': ['details'],
        }
    }

    name = StringField(required=True)
    aliases = ListField(StringField())
    identifiers = ListField(EmbeddedDocumentField(EmbeddedActorIdentifier))
    intended_effects = ListField(StringField())
    motivations = ListField(StringField())
    sophistications = ListField(StringField())
    threat_types = ListField(StringField())

    def migrate(self):
        migrate_actor(self)

    def generate_identifiers_list(self, username=None):
        """
        Create a list of dictionaries with Identifier information which can be
        used for rendering in a template.

        :returns: list
        """

        result = []
        if not username:
            return result
        sources = user_sources(username)
        for i in self.identifiers:
            it = ActorIdentifier.objects(id=i.identifier_id,
                                         source__name__in=sources).first()
            if it:
                d = {}
                d['analyst'] = i.analyst
                d['confidence'] = i.confidence
                d['id'] = i.identifier_id
                d['type'] = it.identifier_type
                d['name'] = it.name
                d['date'] = i.date
                result.append(d)
        return result

    def attribute_identifier(self, identifier_type=None, identifier=None,
                             confidence='low', analyst=None):
        """
        Attribute an identifier.

        :param identifier_type: The type of Identifier.
        :type identifier_type: str
        :param identifier: The identifier value.
        :type identifier: str
        :param confidence: The confidence level of the attribution.
        :type confidence: str
        :param analyst: The analyst attributing this identifier.
        :type analyst: str
        """

        if analyst and identifier_type and identifier:
            # We don't use source restriction because if they are adding this on
            # their own, we would just append their org as a new source
            identifier = ActorIdentifier.objects(name=identifier).first()

            if not identifier:
                return

            found = False
            for ident in self.identifiers:
                if str(identifier.id) == str(ident.identifier_id):
                    found = True
                    break

            # Only add if it's not already there
            if not found:
                e = EmbeddedActorIdentifier()
                e.analyst = analyst
                e.confidence = confidence
                e.identifier_id = str(identifier.id)
                self.identifiers.append(e)

    def update_aliases(self, aliases):
        """
        Update the aliases on an Actor.

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

    def update_tags(self, tag_type, tags):
        """
        Update the tags on an Actor.

        :param tag_type: The type of tag we are updating.
        :type tag_type: str
        :param tags: The tags we are setting.
        :type tags: list
        """

        if isinstance(tags, basestring):
            tags = tags.split(',')
        tags = [t.strip() for t in tags if t != '']
        existing_tags = None
        if tag_type == 'ActorIntendedEffect':
            if len(tags) < len(self.intended_effects):
                self.intended_effects = tags
            else:
                existing_tags = self.intended_effects
        elif tag_type == 'ActorMotivation':
            if len(tags) < len(self.motivations):
                self.motivations = tags
            else:
                existing_tags = self.motivations
        elif tag_type == 'ActorSophistication':
            if len(tags) < len(self.sophistications):
                self.sophistications = tags
            else:
                existing_tags = self.sophistications
        elif tag_type == 'ActorThreatType':
            if len(tags) < len(self.threat_types):
                self.threat_types = tags
            else:
                existing_tags = self.threat_types
        else:
            return
        if existing_tags is not None:
            for t in tags:
                if t not in existing_tags:
                    existing_tags.append(t)

    def set_identifier_confidence(self, identifier_id, confidence):
        """
        Set the confidence level on an attribution.

        :param identifier_id: The ObjectId of the identifier.
        :type identifier_id: str
        :param confidence: The confidence to set.
        :type confidence: str
        """

        if identifier_id and confidence:
            c = 0
            for i in self.identifiers:
                if i.identifier_id == identifier_id:
                    self.identifiers[c].confidence = confidence
                    break
                c += 1

    def remove_attribution(self, identifier_id):
        """
        Remove attribution from this Actor.

        :param identifier_id: The ObjectId of the identifier to remove.
        """

        if identifier_id:
            c = 0
            for i in self.identifiers:
                if i.identifier_id == identifier_id:
                    del self.identifiers[c]
                    break
                c += 1

    def to_stix_actor(self):
        """
        Create a STIX Actor.
        """

        from stix.threat_actor import ThreatActor
        ta = ThreatActor()
        ta.title = self.name
        ta.description = self.description
        for tt in self.threat_types:
            ta.add_type(tt)
        for m in self.motivations:
            ta.add_motivation(m)
        for ie in self.intended_effects:
            ta.add_intended_effect(ie)
        for s in self.sophistications:
            ta.add_sophistication(s)
        #for i in self.identifiers:
        return (ta, self.releasability)

    @classmethod
    def from_stix(cls, stix_threat_actor):
        """
        Converts a STIX ThreatActor to a CRITs Actor.

        :param stix_package: A stix package.
        :type stix_package: :class:`stix.core.STIXPackage`
        :returns: None, :class:`crits.actors.actor.Actor'
        """

        from stix.threat_actor import ThreatActor

        if isinstance(stix_threat_actor, ThreatActor):
            actor = cls()
            actor.name = str(stix_threat_actor.title)
            actor.description = str(stix_threat_actor.description)
            for sophistication in stix_threat_actor.sophistications:
                actor.sophistications.append(str(sophistication.value))
            for motivation in stix_threat_actor.motivations:
                actor.motivations.append(str(motivation.value))
            for threat_type in stix_threat_actor.types:
                actor.threat_types.append(str(threat_type.value))
            for intended_effect in stix_threat_actor.intended_effects:
                actor.intended_effects.append(str(intended_effect.value))
            return actor
            # for identifier in stix_threat_actor.where_the_heck_do_they_go?
        else:
            return None
