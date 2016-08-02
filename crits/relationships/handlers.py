import datetime

from dateutil.parser import parse

from crits.core.class_mapper import class_from_id

def get_relationships(obj=None, type_=None, id_=None, analyst=None):
    """
    Get relationships for a top-level object.

    :param obj: The top-level object to get relationships for.
    :type obj: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param type_: The top-level object type to get relationships for.
    :type type_: str
    :param id_: The ObjectId of the top-level object.
    :type id_: str
    :param analyst: The user requesting the relationships.
    :type analyst: str
    :returns: dict
    """

    if obj:
        return obj.sort_relationships("%s" % analyst, meta=True)
    elif type_ and id_:
        obj = class_from_id(type_, id_)
        if not obj:
            return {}
        return obj.sort_relationships("%s" % analyst, meta=True)
    else:
        return {}

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

    try:
        # forge relationship
        results = class_.add_relationship(right_class, rel_type, rel_date,
                                          user, rel_confidence, rel_reason)
    except Exception as e:
        return {'success': False, 'message': e}

    if results['success']:
        class_.update(add_to_set__relationships=results['message'])
        if get_rels:
            results['relationships'] = class_.sort_relationships("%s" % user,
                                                                 meta=True)
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

    # delete relationship
    if right_class:
        results = left_class.delete_relationship(rel_item=right_class,
                                    rel_type=rel_type,
                                    rel_date=rel_date,
                                    analyst=analyst)
        right_class.save(username=analyst)
    else:
        if right_type and right_id:
            results = left_class.delete_relationship(type_=right_type,
                                        rel_id=right_id,
                                        rel_type=rel_type,
                                        rel_date=rel_date,
                                        analyst=analyst)
        else:
            return {'success': False,
                    'message': "Need a valid right type and id"}
    if results['success']:
        left_class.save(username=analyst)
        if get_rels:
            results['relationships'] = left_class.sort_relationships("%s" % analyst, meta=True)
    return results

def update_relationship_types(left_class=None, right_class=None,
                              left_type=None, left_id=None,
                              right_type=None, right_id=None,
                              rel_type=None, rel_date=None,
                              new_type=None,analyst=None):
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

    # update relationship
    if right_class:
        results = left_class.edit_relationship_type(rel_item=right_class,
                                                    rel_type=rel_type,
                                                    rel_date=rel_date,
                                                    new_type=new_type,
                                                    analyst=analyst)
        left_class.save(username=analyst)
        right_class.save(username=analyst)
    else:
        if right_type and right_id:
            results = left_class.edit_relationship_type(type_=right_type,
                                                        rel_id=right_id,
                                                        rel_type=rel_type,
                                                        rel_date=rel_date,
                                                        new_type=new_type,
                                                        analyst=analyst)
            left_class.save(username=analyst)
        else:
            return {'success': False,
                    'message': "Need a valid right type and id"}

    return results


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
        else:
            return {'success': False,
                    'message': "Need a valid left type and id"}

    # update relationship
    if right_class:
        results = left_class.edit_relationship_confidence(rel_item=right_class,
                                                    rel_type=rel_type,
                                                    rel_date=rel_date,
                                                    new_confidence=new_confidence,
                                                    analyst=analyst)
        left_class.save(username=analyst)
        right_class.save(username=analyst)
    else:
        if right_type and right_id:
            results = left_class.edit_relationship_confidence(type_=right_type,
                                                        rel_id=right_id,
                                                        rel_type=rel_type,
                                                        rel_date=rel_date,
                                                        new_confidence=new_confidence,
                                                        analyst=analyst)
            left_class.save(username=analyst)
        else:
            return {'success': False,
                    'message': "Need a valid right type and id"}

    return results

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
        else:
            return {'success': False,
                    'message': "Need a valid left type and id"}

    # update relationship
    if right_class:
        results = left_class.edit_relationship_reason(rel_item=right_class,
                                                    rel_type=rel_type,
                                                    rel_date=rel_date,
                                                    new_reason=new_reason,
                                                    analyst=analyst)
        left_class.save(username=analyst)
        right_class.save(username=analyst)
    else:
        if right_type and right_id:
            results = left_class.edit_relationship_reason(type_=right_type,
                                                        rel_id=right_id,
                                                        rel_type=rel_type,
                                                        rel_date=rel_date,
                                                        new_reason=new_reason,
                                                        analyst=analyst)
            left_class.save(username=analyst)
        else:
            return {'success': False,
                    'message': "Need a valid right type and id"}

    return results

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

    if new_date is None or new_date == 'None':
        new_date = None
    elif isinstance(new_date, basestring) and new_date != '':
        new_date = parse(new_date, fuzzy=True)
    elif not isinstance(new_date, datetime.datetime):
        new_date = None

    if not left_class:
        if left_type and left_id:
            left_class = class_from_id(left_type, left_id)
            if not left_class:
                return {'success': False,
                        'message': "Unable to get object."}
        else:
            return {'success': False,
                    'message': "Need a valid left type and id"}

    # update relationship
    if right_class:
        results = left_class.edit_relationship_date(rel_item=right_class,
                                                    rel_type=rel_type,
                                                    rel_date=rel_date,
                                                    new_date=new_date,
                                                    analyst=analyst)
        left_class.save(username=analyst)
        right_class.save(username=analyst)
    else:
        if right_type and right_id:
            results = left_class.edit_relationship_date(type_=right_type,
                                                        rel_id=right_id,
                                                        rel_type=rel_type,
                                                        rel_date=rel_date,
                                                        new_date=new_date,
                                                        analyst=analyst)
            left_class.save(username=analyst)
        else:
            return {'success': False,
                    'message': "Need a valid right type and id"}

    return results
