from mongoengine.base import ValidationError

from crits.core.class_mapper import class_from_id
from crits.core.crits_mongoengine import EmbeddedLocation
from crits.core.handlers import get_item_names

from crits.locations.location import Location

def get_location_names_list(active):
    listing = get_item_names(Location, bool(active))
    return [c.name for c in listing]

def location_add(id_, type_, location_type, location_name, user,
                 description=None, latitude=None, longitude=None):
    """
    Add a Location to a top-level object.

    :param id_: The ObjectId of the TLO to add this location to.
    :type id_: str
    :param type_: The TLO type.
    :type type_: str
    :param location_type: The type of location based on origin or destination.
    :type location_type: str
    :param location: The location.
    :type location: str
    :param user: The user attributing this Location.
    :type user: str
    :param description: Description of this attribution.
    :type description: str
    :param latitude: The latitude of the location.
    :type latitude: str
    :param longitude: The longitude of the location.
    :type longitude: str
    :returns: dict with keys:
        'success' (boolean),
        'html' (str) if successful,
        'message' (str).
    """

    if id_ and type_:
        # Verify the document exists.
        obj = class_from_id(type_, id_)
        if not obj:
            return {'success': False, 'message': 'Cannot find %s.' % type_}
    else:
        return {'success': False,
                'message': 'Object type and ID must be provided.'}

    # Create the embedded location.
    location = EmbeddedLocation(
        location_type = location_type,
        location = location_name,
        description = description,
        latitude = latitude,
        longitude = longitude,
        analyst = user
    )
    location.date = location.date.replace(microsecond=0)
    result = obj.add_location(location)

    if result['success']:
        try:
            obj.save(username=user)
            html = obj.format_location(location, user)
            return {'success': True,
                    'html': html,
                    'message': result['message']}
        except ValidationError, e:
            return {'success': False,
                    'message': "Invalid value: %s" % e}
    return {'success': False,
            'message': result['message']}

def location_remove(id_, type_, location_name, location_type, date, user):
    """
    Remove location attribution.

    :param id_: The ObjectId of the TLO.
    :type id_: str
    :param type_: The type of TLO.
    :type type_: str
    :param location_name: The location to remove.
    :type location_name: str
    :param location_type: The location type to remove.
    :type location_type: str
    :param date: The location date to remove.
    :type date: str
    :param user: The user removing this attribution.
    :type user: str
    :returns: dict with key 'success' (boolean) and 'message' (str) if failed.

    """

    # Verify the document exists.
    crits_object = class_from_id(type_, id_)
    if not crits_object:
        return {'success': False, 'message': 'Cannot find %s.' % type_}

    crits_object.remove_location(location_name, location_type, date)
    try:
        crits_object.save(username=user)
        return {'success': True}
    except ValidationError, e:
        return {'success': False, 'message': "Invalid value: %s" % e}

def location_edit(type_, id_, location_name, location_type, date, user,
                  description=None, latitude=None, longitude=None):
    """
    Update a location.

    :param type_: Type of TLO.
    :type type_: str
    :param id_: The ObjectId of the TLO.
    :type id_: str
    :param location_name: The name of the location to change.
    :type location_name: str
    :param location_type: The type of the location to change.
    :type location_type: str
    :param date: The location date to edit.
    :type date: str
    :param user: The user setting the new description.
    :type user: str
    :param description: The new description.
    :type description: str
    :param latitude: The new latitude.
    :type latitude: str
    :param longitude: The new longitude.
    :type longitude: str
    :returns: dict with key 'success' (boolean) and 'message' (str) if failed.
    """

    crits_object = class_from_id(type_, id_)
    if not crits_object:
        return {'success': False, 'message': 'Cannot find %s.' % type_}

    crits_object.edit_location(location_name,
                               location_type,
                               date,
                               description=description,
                               latitude=latitude,
                               longitude=longitude)
    try:
        crits_object.save(username=user)
        return {'success': True}
    except ValidationError, e:
        return {'success': False, 'message': "Invalid value: %s" % e}
