import datetime

from dateutil.parser import parse
from crits.relationships.relationship import Relationship,EmbeddedRelationship
from crits.core.class_mapper import class_from_id, class_from_type
from crits.vocabulary.relationships import RelationshipTypes
from crits.core.mongo_tools import mongo_connector
from crits.core.user_tools import user_sources

META_QUERY = {
            'Actor': ('name', 'campaign'),
            'Backdoor': ('name', 'version', 'campaign'),
            'Campaign': ('name'),
            'Certificate': ('md5', 'filename', 'description', 'campaign'),
            'Domain': ('domain'),
            'Email': ('from_address', 'sender', 'subject', 'campaign'),
            'Event': ('title', 'event_type', 'description', 'campaign'),
            'Exploit': ('name', 'cve', 'campaign'),
            'Indicator': ('type', 'value', 'campaign', 'actions'),
            'IP': ('ip', 'campaign'),
            'PCAP': ('md5', 'filename', 'description', 'campaign'),
            'RawData': ('title', 'data_type', 'tool', 'description',
                        'version', 'campaign'),
            'Sample': ('md5', 'filename', 'mimetype', 'size', 'campaign'),
            'Signature': ('title', 'data_type', 'description', 'version', 'campaign'),
            'Target': ('firstname', 'lastname', 'email_address', 'email_count'),
        }

def get_relationships(obj=None, type_=None, id_=None, username=None, sorted=True, meta=False):
    """
    Get relationships for a top-level object.  

    :param obj: The top-level object to get relationships for.
    :type obj: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param type_: The top-level object type to get relationships for.
    :type type_: str
    :param id_: The ObjectId of the top-level object.
    :type id_: str
    :param username: The user requesting the relationships.
    :type username: str
    :param sorted: The way the relationships are returned.
    :type sorted: bool
    :param meta: Return metadata of related TLOs.
    :type meta: bool
    :returns: dict or list
    """

    tlo = None 
    if obj:
        tlo = obj
    elif type_ and id_:
        obj = class_from_id(type_, id_)
        if obj:
            tlo = obj
    if tlo:
        relationship_col = mongo_connector('relationships')
        relationships = relationship_col.find({ '$or': [{'left_obj.obj_id': tlo.id,'left_obj.obj_type':tlo._meta['crits_type']},
                                                        {'right_obj.obj_id': tlo.id,'right_obj.obj_type':tlo._meta['crits_type']}]})

        source = []
        if username:
            sources = user_sources(username)
            if not sources:
                    return []

        sorted_related_tlos = {}
        sorted_relationships = {}
        for rel in relationships:
            if rel['left_obj']['obj_id'] == tlo.id and rel['left_obj']['obj_type'] == tlo._meta['crits_type']:
                del rel['left_obj']
                rel['other_obj'] = rel.pop("right_obj")
            elif rel['right_obj']['obj_id'] == tlo.id and rel['right_obj']['obj_type'] == tlo._meta['crits_type']:
                del rel['right_obj']
                rel['other_obj'] = rel.pop("left_obj")
            else:
                continue
            sorted_relationships.setdefault(rel['other_obj']['obj_type'],[]).append(rel)
            sorted_related_tlos.setdefault(rel['other_obj']['obj_type'],{})[rel['other_obj']['obj_id']] = {}
        count = 0

        for tlo_type in sorted_related_tlos:
            tlo_ids = sorted_related_tlos[tlo_type].keys()
            obj_class = class_from_type(tlo_type)
            collection_name = obj_class._meta['collection']
            obj_collection = mongo_connector(collection_name)
            
            fields = {'_id' : 1}
            for meta_field in META_QUERY.get(tlo_type):
                fields[meta_field] = 1
            
            # Sanitize based on user's access to sources, except for TLOs which do not have sources.
            # If no username is provided, do not sanitize.
            if username and tlo_type not in ["Campaign", "Target"]:
                pymongo_query = { '_id':{ '$in': tlo_ids },'source.name' : {'$in':sources}}
            else:
                pymongo_query = { '_id':{ '$in': tlo_ids }}
                
            query_result = obj_collection.find(pymongo_query,fields)
            
            for obj in query_result:
                sorted_related_tlos.setdefault(tlo_type,{})
                sorted_related_tlos[tlo_type][obj['_id']] = obj
                count += 1

            if meta:
                for tlo_type,rel_list in sorted_relationships.iteritems():
                    for rel in rel_list:
                        other_tlo = sorted_related_tlos[tlo_type][rel['other_obj']['obj_id']]
                        rel.update(other_tlo)
                        if "_id" in rel:
                            rel["id"] = rel["_id"]
                        if "type" in rel:
                            rel["ind_type"] = rel["type"]
                            del rel["type"]
                        if "value" in rel:
                            rel["ind_value"] = rel["value"]
                            del rel["value"]
                        rel.update(other_tlo)
        if sorted:
            # Return sorted dict.  "Other" needs to be addressed above.
            sorted_relationships['Count'] = count
            sorted_relationships['Other'] = 0
            return sorted_relationships
        else:
            # Return list of rels.
            result = []
            for rels in sorted_relationships.values():
                result += rels
            return result
    else:
        return []

def find_existing_relationship(left_obj,right_obj,rel_date=None,get_rels=False):
    """
    Find existing relationships via pymongo.  

    :param left_obj: The top-level object to get relationships for.
    :type left_obj: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param right_obj: The top-level object to get relationships for.
    :type right_obj: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param rel_date: The date this relationship applies.
    :type rel_date: datetime.datetime
    :param get_rels: Return the relationships after finding duplicates.
    :type get_rels: boolean
    :returns: dict with keys:
              "success" (boolean)
              "message" (str if fail, list if getrels)
    """
    pymongo_query = { '$or': [{'left_obj.obj_id': left_obj.obj_id,
                                 'left_obj.obj_type':left_obj.obj_type,
                                 'left_obj.rel_type': left_obj.rel_type,
                                 'right_obj.obj_id': right_obj.obj_id,
                                 'right_obj.obj_type':right_obj.obj_type,
                                 'right_obj.rel_type': right_obj.rel_type,
                                 },
                                {'left_obj.obj_id': right_obj.obj_id,
                                 'left_obj.obj_type':right_obj.obj_type,
                                 'left_obj.rel_type': right_obj.rel_type,
                                 'right_obj.obj_id': left_obj.obj_id,
                                 'right_obj.obj_type':left_obj.obj_type,
                                 'right_obj.rel_type': left_obj.rel_type,
                                }]
                     }
    if rel_date:
        pymongo_query['$or'][0]['relationship_date'] = rel_date
        pymongo_query['$or'][1]['relationship_date'] = rel_date
        
    relationship_col = mongo_connector('relationships')
    relationships = relationship_col.find(pymongo_query)
    
    if relationships.count() > 0:
        if get_rels:
            return {'success' : True, 'message': list(relationships) }
        else:
            return {'success' : True, 'message': 'Duplicate relationship exists.' }
    else:
        return {'success' : False, 'message': 'No duplicate found.' }

def forge_relationship(type_=None, id_=None,
                       class_=None, right_type=None,
                       right_id=None, right_class=None,
                       rel_type=None, rel_date=None,
                       user=None, rel_reason="",
                       rel_confidence='unknown', get_rels=False, **kwargs):
    """
    Forge a relationship between two top-level objects.

    :param type_: The type of first top-level object to relate to.
    :type type_: str
    :param id_: The ObjectId of the first top-level object.
    :type id_: str
    :param class_: The first top-level object to relate to.
    :type class_: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param right_type: The type of second top-level object to relate to.
    :type right_type: str
    :param right_id: The ObjectId of the second top-level object.
    :type right_id: str
    :param right_class: The second top-level object to relate to.
    :type right_class: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param rel_type: The type of relationship.
    :type rel_type: str
    :param rel_date: The date this relationship applies.
    :type rel_date: datetime.datetime
    :param user: The user forging this relationship.
    :type user: str
    :param rel_reason: The reason for the relationship.
    :type rel_reason: str
    :param rel_confidence: The confidence of the relationship.
    :type rel_confidence: str
    :param get_rels: Return the relationships after forging.
    :type get_rels: boolean
    :returns: dict with keys:
              "success" (boolean)
              "message" (str if fail, EmbeddedObject if success)
              "relationships" (dict)
    """
    new_relationship = Relationship()
    if rel_date == 'None':
        rel_date = None
    elif isinstance(rel_date, basestring) and rel_date != '':
        rel_date = parse(rel_date, fuzzy=True)
    elif not isinstance(rel_date, datetime.datetime):
        rel_date = None

    if not class_:
        if type_ and id_:
            class_ = class_from_id(type_, id_)
        if not class_:
            return {'success': False, 'message': "Failed to get left TLO"}
    if not right_class:
        if right_type and right_id:
            right_class = class_from_id(right_type, right_id)
        if not right_class:
            return {'success': False, 'message': "Failed to get right TLO"}

    if class_ == right_class:
        return {'success': False,
                'message': 'Cannot forge relationship to oneself'}

    # get reverse relationship
    rev_type = RelationshipTypes.inverse(rel_type)
    if rev_type is None:
        return {'success': False,
                'message': 'Could not find relationship type'}

    left_obj = EmbeddedRelationship()
    left_obj.obj_type = class_._meta['crits_type']
    left_obj.obj_id = class_.id
    left_obj.rel_type = rel_type
    
    right_obj = EmbeddedRelationship()
    right_obj.obj_type = right_class._meta['crits_type']
    right_obj.obj_id = right_class.id
    right_obj.rel_type = RelationshipTypes.inverse(rel_type)

    new_relationship.left_obj = left_obj
    new_relationship.right_obj = right_obj
    new_relationship.relationship_date = rel_date
    new_relationship.rel_reason = rel_reason
    new_relationship.rel_confidence = rel_confidence
    new_relationship.analyst = user 
    
    # Check to see if the relationship already exists
    duplicate = find_existing_relationship(left_obj,right_obj,rel_date=rel_date,get_rels=False)
    
    if duplicate['success']:
         return {'success': False, 'message': 'Relationship already exists'}
    try:
        new_relationship.save()
        if left_obj.obj_type == "Backdoor" or right_obj.obj_type == "Backdoor":
            forge_backdoor_relationships(class_,right_class,rel_type,rel_date,user,
                                         rel_reason,rel_confidence)
    except Exception as e:
        return {'success': False, 'message': e}

    results = {'success' : True}
    if get_rels:
        results['relationships'] = get_relationships(obj=class_,username=user,
                                                     sorted=True, meta=True)
    return results

def forge_backdoor_relationships(left_obj,right_obj,rel_type,rel_date,analyst,rel_reason,rel_confidence):
    """
    Forge a relationship between a backdoor and its parent.

    :param left_obj: The first top-level object to relate to.
    :type left_obj: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param right_obj: The second top-level object to relate to.
    :type right_obj: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param rel_type: The type of relationship.
    :type rel_type: str
    :param rel_date: The date this relationship applies.
    :type rel_date: datetime.datetime
    :param analyst: The user forging this relationship.
    :type analyst: str
    :param rel_reason: The reason for the relationship.
    :type rel_reason: str
    :param rel_confidence: The confidence of the relationship.
    :type rel_confidence: str
    :returns: dict with keys:
              "success" (boolean)
              "message" (str if fail, EmbeddedObject if success)
              "relationships" (dict)
    """
    
    # In case of relating to a versioned backdoor we also want to relate to
    # the family backdoor.
    left_obj_type = left_obj._meta['crits_type']
    right_obj_type = right_obj._meta['crits_type']

    # If both are not backdoors, just return
    if left_obj_type != 'Backdoor' and right_obj_type != 'Backdoor':
        return {'success': False, 'message': 'Neither object is a backdoor.'}


    # If either object is a family backdoor, don't go further.
    if ((left_obj_type == 'Backdoor' and left_obj.version == '') or
        (right_obj_type == 'Backdoor' and right_obj.version == '')):
        return {'success': False, 'message': 'Related TLO is already a family backdoor.'}

    # If one is a versioned backdoor and the other is a family backdoor,
    # don't go further.
    if ((left_obj_type == 'Backdoor' and left_obj.version != '' and
         right_obj_type == 'Backdoor' and right_obj.version == '') or
        (right_obj_type == 'Backdoor' and right_obj.version != '' and
         left_obj_type == 'Backdoor' and left_obj.version == '')):
        return {'success': False, 'message': 'Related TLO is already a family backdoor.'}

    # Figure out which is the backdoor object.
    if left_obj_type == 'Backdoor':
        bd = left_obj
        other = right_obj
    else:
        bd = right_obj
        other = left_obj

    # Find corresponding family backdoor object.
    klass = class_from_type('Backdoor')
    family = klass.objects(name=bd.name, version='').first()
    if family:
        forge_relationship(class_=family,
                           rel_type=rel_type,
                           rel_date=rel_date,
                           analyst=analyst,
                           rel_confidence=rel_confidence,
                           rel_reason=rel_reason)
        other.save(user=analyst)
    return results

def delete_all_relationships(left_class=None, left_type=None,
                             left_id=None, analyst=None):
    """
    Delete all relationships for this top-level object.

    :param left_class: The top-level object to delete relationships for.
    :type left_class: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param left_type: The type of the top-level object.
    :type left_type: str
    :param left_id: The ObjectId of the top-level object.
    :type left_id: str
    :param analyst: The user deleting these relationships.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    if not left_class:
        if left_type and left_id:
            left_class = class_from_id(left_type, left_id)
            if not left_class:
                return {'success': False,
                        'message': "Unable to get object."}
        else:
            return {'success': False,
                    'message': "Need a valid left type and id"}

    return left_class.delete_all_relationships()

def delete_relationship(left_class=None, right_class=None,
                       left_type=None, left_id=None,
                       right_type=None, right_id=None,
                       rel_type=None, rel_date=None,
                       analyst=None, get_rels=True):
    """
    Delete a relationship between two top-level objects.

    :param left_class: The first top-level object.
    :type left_class: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param right_class: The second top-level object.
    :type right_class: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param left_type: The type of first top-level object.
    :type left_type: str
    :param left_id: The ObjectId of the first top-level object.
    :type left_id: str
    :param right_type: The type of second top-level object.
    :type right_type: str
    :param right_id: The ObjectId of the second top-level object.
    :type right_id: str
    :param rel_type: The type of relationship.
    :type rel_type: str
    :param rel_date: The date this relationship applies.
    :type rel_date: datetime.datetime
    :param analyst: The user deleting this relationship.
    :type analyst: str
    :param get_rels: Return the relationships after forging.
    :type get_rels: boolean
    :returns: dict with keys "success" (boolean) and "message" (str if
                failed, dict if successful)
    """


    if rel_date is None or rel_date == 'None':
        rel_date = None
    elif isinstance(rel_date, basestring) and rel_date != '':
        rel_date = parse(rel_date, fuzzy=True)
    elif not isinstance(rel_date, datetime.datetime):
        rel_date = None

    if not left_class:
        if left_type and left_id:
            left_class = class_from_id(left_type, left_id)
            if not left_class:
                return {'success': False,
                        'message': "Unable to get object."}
        else:
            return {'success': False,
                    'message': "Need a valid left type and id"}
    if not right_class:
        if right_type and right_id:
            right_class = class_from_id(right_type, right_id)
            if not right_class:
                return {'success': False,
                        'message': "Unable to get object."}
        else:
            return {'success': False,
                    'message': "Need a valid right type and id"}

    rev_type = RelationshipTypes.inverse(rel_type)

    left_obj = EmbeddedRelationship()
    left_obj.obj_type = left_class._meta['crits_type']
    left_obj.obj_id = left_class.id
    left_obj.rel_type = rev_type

    right_obj = EmbeddedRelationship()
    right_obj.obj_type = right_class._meta['crits_type']
    right_obj.obj_id = right_class.id
    right_obj.rel_type = rel_type
    existing_rels = find_existing_relationship(left_obj,right_obj,rel_date=rel_date,get_rels=True)
    
    if not existing_rels['success']:
        return {'success': False,
                'message': 'Could not find existing relationship.'}
    reld = existing_rels['message'][0]
    rel = Relationship.objects(id=reld['_id']).first()
    
    results = rel.modify_relationship(left_obj=left_class,modification="delete", 
                                   analyst=analyst)
    if results['success']:
        left_class.save(username=analyst)
        if get_rels:
            results['relationships'] = get_relationships(obj=left_class,username=analyst,sorted=True, meta=True)
    return results

def update_relationship_types(left_class=None, right_class=None,
                              left_type=None, left_id=None,
                              right_type=None, right_id=None,
                              rel_type=None, rel_date=None,
                              new_type=None, analyst=None):
    """
    Update the relationship type between two top-level objects.

    :param left_class: The first top-level object.
    :type left_class: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param right_class: The second top-level object.
    :type right_class: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param left_type: The type of first top-level object.
    :type left_type: str
    :param left_id: The ObjectId of the first top-level object.
    :type left_id: str
    :param right_type: The type of second top-level object.
    :type right_type: str
    :param right_id: The ObjectId of the second top-level object.
    :type right_id: str
    :param rel_type: The type of relationship.
    :type rel_type: str
    :param rel_date: The date this relationship applies.
    :type rel_date: datetime.datetime
    :param new_type: The new type of relationship.
    :type new_type: str
    :param analyst: The user updating this relationship.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """
    if rel_date is None or rel_date == 'None':
        rel_date = None
    elif isinstance(rel_date, basestring) and rel_date != '':
        rel_date = parse(rel_date, fuzzy=True)
    elif not isinstance(rel_date, datetime.datetime):
        rel_date = None

    if not left_class:
        if left_type and left_id:
            left_class = class_from_id(left_type, left_id)
            if not left_class:
                return {'success': False,
                        'message': "Unable to get object."}
        else:
            return {'success': False,
                    'message': "Need a valid left type and id"}
    if not right_class:
        if right_type and right_id:
            right_class = class_from_id(right_type, right_id)
            if not right_class:
                return {'success': False,
                        'message': "Unable to get object."}
        else:
            return {'success': False,
                    'message': "Need a valid right type and id"}

    rev_type = RelationshipTypes.inverse(rel_type)

    left_obj = EmbeddedRelationship()
    left_obj.obj_type = left_class._meta['crits_type']
    left_obj.obj_id = left_class.id
    left_obj.rel_type = rev_type

    right_obj = EmbeddedRelationship()
    right_obj.obj_type = right_class._meta['crits_type']
    right_obj.obj_id = right_class.id
    right_obj.rel_type = rel_type
    existing_rels = find_existing_relationship(left_obj,right_obj,rel_date=rel_date,get_rels=True)
    
    if not existing_rels['success']:
        return {'success': False,
                'message': 'Could not find existing relationship.'}
    
    reld = existing_rels['message'][0]
    rel = Relationship.objects(id=reld['_id']).first()
    
    return rel.modify_relationship(left_obj=left_class, new_type=new_type,
                                   modification="type", analyst=analyst)

def update_relationship_confidences(left_class=None, right_class=None,
                                    left_type=None, left_id=None,
                                    right_type=None, right_id=None,
                                    rel_type=None, rel_date=None,
                                    new_type=None,analyst=None,
                                    new_confidence='unknown'):
    """
    Update the relationship type between two top-level objects.

    :param left_class: The first top-level object.
    :type left_class: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param right_class: The second top-level object.
    :type right_class: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param left_type: The type of first top-level object.
    :type left_type: str
    :param left_id: The ObjectId of the first top-level object.
    :type left_id: str
    :param right_type: The type of second top-level object.
    :type right_type: str
    :param right_id: The ObjectId of the second top-level object.
    :type right_id: str
    :param rel_type: The type of relationship.
    :type rel_type: str
    :param rel_date: The date this relationship applies.
    :type rel_date: datetime.datetime
    :param analyst: The user updating this relationship.
    :type analyst: str
    :param new_confidence: The new confidence level.
    :type new_confidence: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    if rel_date is None or rel_date == 'None':
        rel_date = None
    elif isinstance(rel_date, basestring) and rel_date != '':
        rel_date = parse(rel_date, fuzzy=True)
    elif not isinstance(rel_date, datetime.datetime):
        rel_date = None

    if not left_class:
        if left_type and left_id:
            left_class = class_from_id(left_type, left_id)
            if not left_class:
                return {'success': False,
                        'message': "Unable to get object."}
        else:
            return {'success': False,
                    'message': "Need a valid left type and id"}
    if not right_class:
        if right_type and right_id:
            right_class = class_from_id(right_type, right_id)
            if not right_class:
                return {'success': False,
                        'message': "Unable to get object."}
        else:
            return {'success': False,
                    'message': "Need a valid right type and id"}

    rev_type = RelationshipTypes.inverse(rel_type)

    left_obj = EmbeddedRelationship()
    left_obj.obj_type = left_class._meta['crits_type']
    left_obj.obj_id = left_class.id
    left_obj.rel_type = rev_type

    right_obj = EmbeddedRelationship()
    right_obj.obj_type = right_class._meta['crits_type']
    right_obj.obj_id = right_class.id
    right_obj.rel_type = rel_type
    existing_rels = find_existing_relationship(left_obj,right_obj,rel_date=rel_date,get_rels=True)
    
    if not existing_rels['success']:
        return {'success': False,
                'message': 'Could not find existing relationship.'}

    reld = existing_rels['message'][0]
    rel = Relationship.objects(id=reld['_id']).first()
    
    return rel.modify_relationship(left_obj=left_class,new_confidence=new_confidence,
                                   modification="confidence", analyst=analyst)

def update_relationship_reasons(left_class=None, right_class=None,
                              left_type=None, left_id=None,
                              right_type=None, right_id=None,
                              rel_type=None, rel_date=None,
                              new_type=None,analyst=None, new_reason="N/A"):
    """
    Update the relationship type between two top-level objects.

    :param left_class: The first top-level object.
    :type left_class: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param right_class: The second top-level object.
    :type right_class: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param left_type: The type of first top-level object.
    :type left_type: str
    :param left_id: The ObjectId of the first top-level object.
    :type left_id: str
    :param right_type: The type of second top-level object.
    :type right_type: str
    :param right_id: The ObjectId of the second top-level object.
    :type right_id: str
    :param rel_type: The type of relationship.
    :type rel_type: str
    :param rel_date: The date this relationship applies.
    :type rel_date: datetime.datetime
    :param analyst: The user updating this relationship.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """
    if rel_date is None or rel_date == 'None':
        rel_date = None
    elif isinstance(rel_date, basestring) and rel_date != '':
        rel_date = parse(rel_date, fuzzy=True)
    elif not isinstance(rel_date, datetime.datetime):
        rel_date = None

    if not left_class:
        if left_type and left_id:
            left_class = class_from_id(left_type, left_id)
            if not left_class:
                return {'success': False,
                        'message': "Unable to get object."}
        else:
            return {'success': False,
                    'message': "Need a valid left type and id"}
    if not right_class:
        if right_type and right_id:
            right_class = class_from_id(right_type, right_id)
            if not right_class:
                return {'success': False,
                        'message': "Unable to get object."}
        else:
            return {'success': False,
                    'message': "Need a valid right type and id"}

    rev_type = RelationshipTypes.inverse(rel_type)

    left_obj = EmbeddedRelationship()
    left_obj.obj_type = left_class._meta['crits_type']
    left_obj.obj_id = left_class.id
    left_obj.rel_type = rev_type

    right_obj = EmbeddedRelationship()
    right_obj.obj_type = right_class._meta['crits_type']
    right_obj.obj_id = right_class.id
    right_obj.rel_type = rel_type
    existing_rels = find_existing_relationship(left_obj,right_obj,rel_date=rel_date,get_rels=True)
    
    if not existing_rels['success']:
        return {'success': False,
                'message': 'Could not find existing relationship.'}

    reld = existing_rels['message'][0]
    rel = Relationship.objects(id=reld['_id']).first()
    
    return rel.modify_relationship(left_obj=left_class,new_reason=new_reason,
                                   modification="reason", analyst=analyst)

def update_relationship_dates(left_class=None, right_class=None,
                              left_type=None, left_id=None,
                              right_type=None, right_id=None,
                              rel_type=None, rel_date=None,
                              new_date=None,analyst=None):
    """
    Update the relationship date between two top-level objects.

    :param left_class: The first top-level object.
    :type left_class: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param right_class: The second top-level object.
    :type right_class: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param left_type: The type of first top-level object.
    :type left_type: str
    :param left_id: The ObjectId of the first top-level object.
    :type left_id: str
    :param right_type: The type of second top-level object.
    :type right_type: str
    :param right_id: The ObjectId of the second top-level object.
    :type right_id: str
    :param rel_type: The type of relationship.
    :type rel_type: str
    :param rel_date: The date this relationship applies.
    :type rel_date: datetime.datetime
    :param new_date: The new date of the relationship.
    :type new_date: str
    :param analyst: The user updating this relationship.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    if rel_date is None or rel_date == 'None':
        rel_date = None
    elif isinstance(rel_date, basestring) and rel_date != '':
        rel_date = parse(rel_date, fuzzy=True)
    elif not isinstance(rel_date, datetime.datetime):
        rel_date = None

    if not left_class:
        if left_type and left_id:
            left_class = class_from_id(left_type, left_id)
            if not left_class:
                return {'success': False,
                        'message': "Unable to get object."}
        else:
            return {'success': False,
                    'message': "Need a valid left type and id"}
    if not right_class:
        if right_type and right_id:
            right_class = class_from_id(right_type, right_id)
            if not right_class:
                return {'success': False,
                        'message': "Unable to get object."}
        else:
            return {'success': False,
                    'message': "Need a valid right type and id"}

    rev_type = RelationshipTypes.inverse(rel_type)

    left_obj = EmbeddedRelationship()
    left_obj.obj_type = left_class._meta['crits_type']
    left_obj.obj_id = left_class.id
    left_obj.rel_type = rev_type

    right_obj = EmbeddedRelationship()
    right_obj.obj_type = right_class._meta['crits_type']
    right_obj.obj_id = right_class.id
    right_obj.rel_type = rel_type
    existing_rels = find_existing_relationship(left_obj,right_obj,rel_date=rel_date,get_rels=True)
    
    if not existing_rels['success']:
        return {'success': False,
                'message': 'Could not find existing relationship.'}

    reld = existing_rels['message'][0]
    rel = Relationship.objects(id=reld['_id']).first()
    
    return rel.modify_relationship(left_obj=left_class,new_date=new_date,
                                   modification="date", analyst=analyst)

