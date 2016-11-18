import datetime
import re

from bson.objectid import ObjectId
from mongoengine import Document, EmbeddedDocument
from mongoengine import ObjectIdField, StringField, ListField, EmbeddedDocumentField
from django.conf import settings
from django.core.urlresolvers import reverse

from crits.core.user import CRITsUser
from crits.core.fields import CritsDateTimeField
from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument
from crits.core.crits_mongoengine import CritsDocumentFormatter, CritsSourceDocument
from crits.core.class_mapper import class_from_type
from crits.vocabulary.relationships import RelationshipTypes

class EmbeddedRelationship(EmbeddedDocument, CritsDocumentFormatter):
    """
    Indicator activity class.
    """
    obj_type = StringField()
    obj_id = ObjectIdField(required=True)
    rel_type = StringField()

class Relationship(CritsDocument, CritsSchemaDocument, Document):
    """
    Relationship Class.
    """

    meta = {
        "collection": settings.COL_RELATIONSHIPS,
        "crits_type": "Relationship",
        "latest_schema_version": 1,
        "schema_doc": {
            'left_obj': 'EmbeddedRelationship for left obj',
            'right_obj': 'EmbeddedRelationship for right obj',
            'date': 'ISODate when this relationship was created',
            'relationship_date' : 'ISOdate of when this relationship occurred.',
            'analyst': 'The analyst, if any, that made this relationship',
            'rel_reason': 'Reason for the relationship',
            'rel_confidence': 'Confidence of the relationship',
        },
        "jtable_opts": {
            'details_url': '',
            'details_url_key': 'id',
            'default_sort': 'date DESC',
            'search_url': '',
            'fields': ["obj_type", "comment", "url_key", "created",
                       "analyst", "source", "id"],
            'jtopts_fields': ["id","date","rel_reason"],
            'hidden_fields': ["id", ],
            'linked_fields': ["analyst"],
            'details_link': 'details',
            'no_sort': ['details', ],
        }

    }

    left_obj =  EmbeddedDocumentField ( EmbeddedRelationship,default=EmbeddedRelationship() )
    right_obj =  EmbeddedDocumentField ( EmbeddedRelationship,default=EmbeddedRelationship() )
    date = CritsDateTimeField()
    relationship_date = CritsDateTimeField()
    analyst = StringField()
    rel_reason = StringField()
    rel_confidence = StringField(default='unknown', required=True)

    def modify_relationship(self,left_obj,new_type=None,
                             new_date=None, new_confidence='unknown',
                             new_reason="N/A", modification=None, analyst=None):
        """
        Modify a relationship to this top-level object.
        :param left_obj: Left object of relationship
        :type left_obj: class which inherits from
                        :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        :param new_type: The new relationship type.
        :type new_type: str
        :param new_date: The new relationship date.
        :type new_date: datetime.datetime
        :param new_confidence: The new confidence.
        :type new_confidence: str
        :param new_reason: The new reason.
        :type new_reason: str
        :param modification: What type of modification this is ("type",
                             "delete", "date", "confidence").
        :type modification: str
        :param analyst: The user forging this relationship.
        :type analyst: str
        :returns: dict with keys "success" (boolean) and "message" (str)
        """

        if modification == "type":
            # get new reverse relationship
            new_rev_type = RelationshipTypes.inverse(new_type)
            if new_rev_type is None:
                return {'success': False,
                        'message': 'Could not find reverse relationship type'}
            if (self.left_obj.obj_id == left_obj.id and 
                self.left_obj.obj_type == left_obj._meta['crits_type']):
                self.right_obj.rel_type = new_type
                self.left_obj.rel_type = new_rev_type
            else:
                self.right_obj.rel_type = new_rev_type
                self.left_obj.rel_type = new_type
        elif modification == "date":
            if isinstance(new_date, basestring):
                new_date = parse(new_date, fuzzy=True)
            self.relationship_date = new_date
        elif modification == "confidence":
            self.rel_confidence = new_confidence
        elif modification == "reason":
            self.rel_reason = new_reason
        elif modification == "delete":
            self.delete(username=analyst)
        else:
            return {'success': False,
                    'message': 'Unknown update type.'}

        if modification == "delete":
            return {'success': True,
                    'message': 'Relationship deleted'}
        else:
            self.save()
            return {'success': True,
                    'message': 'Relationship modified'}
