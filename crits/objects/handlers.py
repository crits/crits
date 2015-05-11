from hashlib import md5

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_ipv4_address, validate_ipv6_address
from django.core.validators import validate_ipv46_address
from django.template.loader import render_to_string
from django.template import RequestContext
from mongoengine.base import ValidationError

from crits.core import form_consts
from crits.core.class_mapper import class_from_id, class_from_type
from crits.core.data_tools import convert_string_to_bool
from crits.core.handlers import get_object_types
from crits.core.handsontable_tools import form_to_dict, get_field_from_label
from crits.core.mongo_tools import put_file, mongo_connector
from crits.core.user_tools import get_user_organization
from crits.indicators.indicator import Indicator
from crits.objects.forms import AddObjectForm
from crits.pcaps.handlers import handle_pcap_file
from crits.relationships.handlers import forge_relationship


def get_objects_type(name=None):
    """
    Get the type of an ObjectType.

    :param name: The name of the ObjectType.
    :type name: str
    :returns: str
    """

    from crits.objects.object_type import ObjectType
    if not name:
        return None
    obj = ObjectType.objects(name=name).first()
    if obj:
        return obj.object_type
    return None

def get_objects_datatype(name, otype):
    """
    Get the datatype of an ObjectType.

    :param name: The name of the ObjectType.
    :type name: str
    :param otype: The type of the ObjectType
    :returns: str
    """

    from crits.objects.object_type import ObjectType
    obj = ObjectType.objects(name=name,
                             object_type=otype).first()
    if obj:
        key = obj.datatype.keys()[0]
        return key
    else:
        return None

def split_object_name_type(full_name):
    """
    Split the name and type into their separate parts.

    :param full_name: The full name of the ObjectType.
    :type full_name: str
    :returns: list of [<name>, <type>]
    """

    split_name = full_name.split(" - ")
    # if len(split_name) == 1, name and type are the same
    return split_name*2 if len(split_name) == 1 else split_name

all_obj_type_choices = [(c[0],
                         c[0],
                         {'datatype':c[1].keys()[0],
                          'datatype_value':c[1].values()[0]}
                         ) for c in get_object_types(False)]

def validate_and_add_new_handler_object(data, rowData, request, errors, row_counter,
                                        is_validate_only=False, is_sort_relationships=False,
                                        cache={}, obj=None):
    """
    Validate an object and then add it to the database.

    :param data: The data for the object.
    :type data: dict
    :param rowData: Data from the row if using mass object upload.
    :type rowData: dict
    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :param errors: List of existing errors to append to.
    :type errors: list
    :param row_counter: Which row we are working on (for error tracking).
    :type row_counter: int
    :param is_validate_only: Only validate.
    :type is_validate_only: bool
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :returns: tuple of (<result>, <errors>, <retVal>)
    """

    result = False
    retVal = {}

    bound_form = parse_row_to_bound_object_form(request, rowData, cache)

    if bound_form.is_valid():
        (result,
         retVal) = add_new_handler_object(data, rowData, request, obj=obj,
                                          is_validate_only=is_validate_only,
                                          is_sort_relationships=is_sort_relationships)
        if not result and 'message' in retVal:
            errors.append("%s #%s - %s" % (form_consts.Common.OBJECTS_DATA,
                                           str(row_counter),
                                           retVal['message']))
    else:
        formdict = cache.get("object_formdict")

        if formdict == None:
            object_form = AddObjectForm(request.user, all_obj_type_choices)
            formdict = form_to_dict(object_form)
            cache['object_formdict'] = formdict

        for name, errorMessages in bound_form.errors.items():
            entry = get_field_from_label(name, formdict)
            if entry == None:
                continue
            for message in errorMessages:
                errors.append("%s #%s - %s - %s" % (form_consts.Common.OBJECTS_DATA,
                                                    str(row_counter),
                                                    name,
                                                    message))
        result = False

    return result, errors, retVal

def add_new_handler_object_via_bulk(data, rowData, request, errors,
                            is_validate_only=False, cache={}, obj=None):
    """
    Bulk add wrapper for the add_new_handler_object() function.
    """

    (result,
     retVal) = add_new_handler_object(data, rowData, request,
                                      is_validate_only=is_validate_only,
                                      is_sort_relationships=True,
                                      cache=cache, obj=obj)
    if not result and 'message' in retVal:
        errors.append(retVal['message'])

    return result, errors, retVal

def add_new_handler_object(data, rowData, request, is_validate_only=False,
                           is_sort_relationships=False, cache={}, obj=None):
    """
    Add an object to the database.

    :param data: The data for the object.
    :type data: dict
    :param rowData: Data from the row if using mass object upload.
    :type rowData: dict
    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :param is_validate_only: Only validate.
    :type is_validate_only: bool
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :param obj: The CRITs top-level object we are adding objects to.
                This is an optional parameter used mainly for performance
                reasons (by not querying mongo if we already have the
                top level-object).
    :type obj: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :returns: tuple (<result>, <retVal>)
    """

    result = False
    retVal = {}
    username = request.user.username

    if data:
        object_type = data.get('object_type')
        value = data.get('value')
        source = data.get('source')
        method = data.get('method')
        reference = data.get('reference')
        otype = data.get('otype')
        oid = data.get('oid')
        add_indicator = data.get('add_indicator')
    elif rowData:
        object_type = rowData.get(form_consts.Object.OBJECT_TYPE)
        value = rowData.get(form_consts.Object.VALUE)
        source = rowData.get(form_consts.Object.SOURCE)
        method = rowData.get(form_consts.Object.METHOD)
        reference = rowData.get(form_consts.Object.REFERENCE)
        otype = rowData.get(form_consts.Object.PARENT_OBJECT_TYPE)
        oid = rowData.get(form_consts.Object.PARENT_OBJECT_ID)
        add_indicator = rowData.get(form_consts.Object.ADD_INDICATOR)

    is_validate_locally = False
    analyst = "%s" % username

    # Default the user source to the user's organization if not specified
    if not source:
        source = cache.get('object_user_source')

        if not source:
            source = get_user_organization(analyst)
            cache['object_user_source'] =  source

    ot_array = object_type.split(" - ")
    object_type = ot_array[0]
    name = ot_array[1] if len(ot_array) == 2 else ot_array[0]

    if (otype == "" or otype == None) or (oid == "" or oid == None):
        is_validate_locally = True

    # TODO file_
    object_result = add_object(otype, oid, object_type, name,
            source, method, reference, analyst, value=value,
            file_=None, add_indicator=add_indicator, get_objects=False,
            obj=obj, is_validate_only=is_validate_only, is_sort_relationships=is_sort_relationships,
            is_validate_locally=is_validate_locally, cache=cache)

    if object_result['success']:
        result = True
        if is_validate_only == False:
            if obj == None:
                obj = class_from_id(otype, oid)

            if obj:
                retVal['secondary'] = {'type': otype, 'id': oid}

                if object_result.get('relationships'):
                    retVal['secondary']['relationships'] = object_result.get('relationships')
    else:
        retVal['message'] = object_result['message']

    return result, retVal

def add_object(type_, oid, object_type, name, source, method,
               reference, analyst, value=None, file_=None,
               add_indicator=False, get_objects=True,
               obj=None, is_sort_relationships=False,
               is_validate_only=False, is_validate_locally=False, cache={}):
    """
    Add an object to the database.

    :param type_: The top-level object type.
    :type type_: str
    :param oid: The ObjectId of the top-level object.
    :type oid: str
    :param object_type: The type of the ObjectType being added.
    :type object_type: str
    :param name: The name of the ObjectType being added.
    :type name: str
    :param source: The name of the source adding this object.
    :type source: str
    :param method: The method for this object.
    :type method: str
    :param reference: The reference for this object.
    :type reference: str
    :param analyst: The user adding this object.
    :type analyst: str
    :param value: The value of the object.
    :type value: str
    :param file_: The file if the object is a file upload.
    :type file_: file handle.
    :param add_indicator: Also add an indicator for this object.
    :type add_indicator: bool
    :param get_objects: Return the formatted list of objects when completed.
    :type get_object: bool
    :param obj: The CRITs top-level object we are adding objects to.
                This is an optional parameter used mainly for performance
                reasons (by not querying mongo if we already have the
                top level-object).
    :type obj: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param is_validate_only: Validate, but do not add to TLO.
    :type is_validate_only: bool
    :param is_validate_locally: Validate, but do not add b/c there is no TLO.
    :type is_validate_locally: bool
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
              "objects" (list),
              "relationships" (list)
    """

    results = {}

    if oid == None:
        oid = ""

    if obj == None:
        obj = class_from_id(type_, oid)

    from crits.indicators.handlers import validate_indicator_value
    (value, error) = validate_indicator_value(value,
                                              object_type + " - " + name)
    if error:
        return {"success": False, "message": error}
    elif is_validate_locally: # no obj provided
        results['success'] = True
        return results

    if not obj:
        results['message'] = "TLO could not be found"
        results['success'] = False
        return results

    try:
        cur_len = len(obj.obj)
        if file_:
            data = file_.read()
            filename = file_.name
            md5sum = md5(data).hexdigest()
            value = md5sum
            reference = filename
        obj.add_object(object_type,
                       name,
                       value,
                       source,
                       method,
                       reference,
                       analyst)

        if is_validate_only == False:
            obj.save(username=analyst)

        new_len = len(obj.obj)
        if new_len > cur_len:
            if not is_validate_only:
                results['message'] = "Object added successfully!"
            results['success'] = True
            if file_:
                # do we have a pcap?
                if data[:4] in ('\xa1\xb2\xc3\xd4',
                                '\xd4\xc3\xb2\xa1',
                                '\x0a\x0d\x0d\x0a'):
                    handle_pcap_file(filename,
                                     data,
                                     source,
                                     user=analyst,
                                     related_id=oid,
                                     related_type=type_)
                else:
                    #XXX: MongoEngine provides no direct GridFS access so we
                    #     need to use pymongo directly.
                    col = settings.COL_OBJECTS
                    grid = mongo_connector("%s.files" % col)
                    if grid.find({'md5': md5sum}).count() == 0:
                        put_file(filename, data, collection=col)
            if add_indicator and is_validate_only == False:
                from crits.indicators.handlers import handle_indicator_ind

                if object_type != name:
                    object_type = "%s - %s" % (object_type, name)

                campaign = obj.campaign if hasattr(obj, 'campaign') else None
                ind_res = handle_indicator_ind(value,
                                               source,
                                               object_type,
                                               analyst,
                                               method,
                                               reference,
                                               add_domain=True,
                                               campaign=campaign,
                                               cache=cache)

                if ind_res['success']:
                    ind = ind_res['object']
                    forge_relationship(left_class=obj,
                                       right_class=ind,
                                       rel_type="Related_To",
                                       analyst=analyst,
                                       get_rels=is_sort_relationships)
                else:
                    results['message'] = "Object was added, but failed to add Indicator." \
                                         "<br>Error: " + ind_res.get('message')

            if is_sort_relationships == True:
                if file_ or add_indicator:
                    # does this line need to be here?
                    # obj.reload()
                    results['relationships'] = obj.sort_relationships(analyst, meta=True)
                else:
                    results['relationships'] = obj.sort_relationships(analyst, meta=True)

        else:
            results['message'] = "Object already exists! [Type: " + object_type + "][Value: " + value + "] "
            results['success'] = False
        if (get_objects):
            results['objects'] = obj.sort_objects()

        results['id'] = str(obj.id)
        return results
    except ValidationError, e:
        return {'success': False,
                'message': str(e)}

def delete_object_file(value):
    """
    In the event this is a file (but not PCAP), clean up after ourselves when
    deleting an object.

    :param value: The value of the object we are deleting.
    :type value: str
    """

    #XXX: MongoEngine provides no direct GridFS access so we
    #     need to use pymongo directly.
    obj_list = ('Campaign',
                'Certificate',
                'Domain',
                'Email',
                'Event',
                'Indicator',
                'IP',
                'PCAP',
                'RawData',
                'Sample',
                'Target',
               )
    # In order to make sure this object isn't tied to more than one top-level
    # object, we need to check the rest of the database. We will at least find
    # one instance, which is the one we are going to be removing. If we find
    # another instance, then we should not remove the object from GridFS.
    count = 0
    found = False
    query = {'objects.value': value}
    for obj in obj_list:
        obj_class = class_from_type(obj)
        c = len(obj_class.objects(__raw__=query))
        if c > 0:
            count += c
            if count > 1:
                found = True
                break
    if not found:
        col = settings.COL_OBJECTS
        grid = mongo_connector("%s.files" % col)
        grid.remove({'md5': value})

def delete_object(type_, oid, object_type, name, value, analyst, get_objects=True):
    """
    Delete an object.

    :param type_: The top-level object type.
    :type type_: str
    :param oid: The ObjectId of the top-level object.
    :type oid: str
    :param object_type: The type of the object to remove.
    :type object_type: str
    :param name: The name of the object to remove.
    :type name: str
    :param value: The value of the object to remove.
    :type value: str
    :param analyst: The user removing this object.
    :type analyst: str
    :param get_objects: Return the list of objects.
    :type get_objects: bool
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
              "objects" (list)
    """

    obj = class_from_id(type_, oid)
    if not obj:
        return {'success': False,
                'message': "Could not find item to remove object from."}
    try:
        cur_len = len(obj.obj)
        obj.remove_object(object_type,
                          name,
                          value)
        obj.save(username=analyst)

        new_len = len(obj.obj)
        result = {}
        if new_len < cur_len:
            result['success'] = True
            result['message'] = "Object removed successfully!"
        else:
            result['success'] = False
            result['message'] = "Could not find object to remove!"

        if (get_objects):
            result['objects'] = obj.sort_objects()
        return result
    except ValidationError, e:
        return {'success': False,
                'message': e}

def update_object_value(type_, oid, object_type, name, value, new_value,
                        analyst):
    """
    Update an object value.

    :param type_: The top-level object type.
    :type type_: str
    :param oid: The ObjectId of the top-level object.
    :type oid: str
    :param object_type: The type of the object to update.
    :type object_type: str
    :param name: The name of the object to update.
    :type name: str
    :param value: The value of the object to update.
    :type value: str
    :param new_value: The new value to use.
    :type new_value: str
    :param analyst: The user removing this object.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    obj = class_from_id(type_, oid)
    if not obj:
        return {'success': False,
                'message': "Could not find item to update object."}
    try:
        obj.update_object_value(object_type,
                                name,
                                value,
                                new_value)
        obj.save(username=analyst)
        return {'success': True, 'message': 'Object value updated successfully.'}
    except ValidationError, e:
        return {'success': False, 'message': e}

def update_object_source(type_, oid, object_type, name, value, new_source,
                         new_method, new_reference, analyst):
    """
    Update an object source.

    :param type_: The top-level object type.
    :type type_: str
    :param oid: The ObjectId of the top-level object.
    :type oid: str
    :param object_type: The type of the object to update.
    :type object_type: str
    :param name: The name of the object to update.
    :type name: str
    :param value: The value of the object to update.
    :type value: str
    :param new_source: The new source to use.
    :type new_source: str
    :param new_method: The new method to use.
    :type new_method: str
    :param new_reference: The new reference to use.
    :type new_reference: str
    :param analyst: The user removing this object.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    obj = class_from_id(type_, oid)
    if not obj:
        return {'success': False,
                'message': "Could not find item to update object."}
    try:
        obj.update_object_source(object_type,
                                 name,
                                 value,
                                 new_source=new_source,
                                 new_method=new_method,
                                 new_reference=new_reference,
                                 analyst=analyst)
        obj.save(username=analyst)
        return {'success': True, 'message': 'Object value updated successfully.'}
    except ValidationError, e:
        return {'success': False, 'message': e}

def create_indicator_from_object(rel_type, rel_id, ind_type, value,
                                 source_name, method, reference, analyst, request):
    """
    Create an indicator out of this object.

    :param rel_type: The top-level object type this object is for.
    :type rel_type: str
    :param rel_id: The ObjectId of the top-level object.
    :param ind_type: The indicator type to use.
    :type ind_type: str
    :param value: The indicator value.
    :type value: str
    :param source_name: The source name for the indicator.
    :type source_name: str
    :param method: The source method for the indicator.
    :type method: str
    :param reference: The source reference for the indicator.
    :type reference: str
    :param analyst: The user creating this indicator.
    :type analyst: str
    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: dict with keys "success" (bool) and "message" (str)
    """

    result = None
    me = class_from_id(rel_type, rel_id)
    if not me:
        result = {'success': False,
                  'message': "Could not find %s" % rel_type}
    elif value == None or value.strip() == "":
        result = {'success':  False,
                  'message':  "Can't create indicator with an empty value field"}
    elif ind_type == None or ind_type.strip() == "":
        result = {'success':  False,
                  'message':  "Can't create indicator with an empty type field"}
    elif source_name == None or source_name.strip() == "":
        result = {'success':  False,
                  'message':  "Can't create indicator with an empty source field"}
    else:
        value = value.lower().strip()
        ind_type = ind_type.strip()
        source_name = source_name.strip()

        create_indicator_result = {}
        ind_tlist = ind_type.split(" - ")
        if ind_tlist[0] == ind_tlist[1]:
            ind_type = ind_tlist[0]
        from crits.indicators.handlers import handle_indicator_ind

        campaign = me.campaign if hasattr(me, 'campaign') else None
        create_indicator_result = handle_indicator_ind(value,
                                                       source_name,
                                                       ind_type,
                                                       analyst,
                                                       method,
                                                       reference,
                                                       add_domain=True,
                                                       campaign=campaign)

        # Check if an error occurred, if it did then return the error result
        if create_indicator_result.get('success', True) == False:
            return create_indicator_result

        indicator = Indicator.objects(ind_type=ind_type,
                                      value=value).first()
        if not indicator:
            result = {'success': False,
                      'message': "Could not create indicator"}
        else:
            results = me.add_relationship(indicator,
                                          "Related_To",
                                          analyst=analyst,
                                          get_rels=True)
            if results['success']:
                me.save(username=analyst)
                relationship= {'type': rel_type, 'value': rel_id}
                message = render_to_string('relationships_listing_widget.html',
                                            {'relationship': relationship,
                                             'nohide': True,
                                             'relationships': results['message']},
                                            RequestContext(request))
                result = {'success': True, 'message': message}
            else:
                message = "Indicator created. Could not create relationship"
                result = {'success': False,
                          'message': message}
    return result

def object_array_to_dict(array, otype, oid):
    """
    Convert an object array to a dictionary.

    :param array: The array.
    :type array: list
    :param otype: The top-level object type.
    :type otype: str
    :param oid: The ObjectId of the top-level object.
    :type oid: str
    :returns: dict
    """

    returnDict = {}
    returnDict[form_consts.Object.OBJECT_TYPE] = array[form_consts.Object.OBJECT_TYPE_INDEX]
    returnDict[form_consts.Object.VALUE] = array[form_consts.Object.VALUE_INDEX]
    returnDict[form_consts.Object.SOURCE] = array[form_consts.Object.SOURCE_INDEX]
    returnDict[form_consts.Object.METHOD] = array[form_consts.Object.METHOD_INDEX]
    returnDict[form_consts.Object.REFERENCE] = array[form_consts.Object.REFERENCE_INDEX]
    returnDict[form_consts.Object.PARENT_OBJECT_TYPE] = otype
    returnDict[form_consts.Object.PARENT_OBJECT_ID] = oid
    returnDict[form_consts.Object.ADD_INDICATOR] = array[form_consts.Object.ADD_INDICATOR_INDEX]

    return returnDict

def parse_row_to_bound_object_form(request, rowData, cache):
    """
    Parse a row from mass object upload into an AddObjectForm.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :param rowData: The row data.
    :type rowData: dict
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :returns: :class:`crits.objects.forms.AddObjectForm`
    """

    bound_form = None

    # TODO fix the hardcoded strings and conversion of types
    # TODO Add common method to convert data to string
    object_type = rowData.get(form_consts.Object.OBJECT_TYPE, "")
    value = rowData.get(form_consts.Object.VALUE, "")
    source = rowData.get(form_consts.Object.SOURCE, "")
    method = rowData.get(form_consts.Object.METHOD, "")
    reference = rowData.get(form_consts.Object.REFERENCE, "")
    otype = rowData.get(form_consts.Object.PARENT_OBJECT_TYPE, "")
    oid = rowData.get(form_consts.Object.PARENT_OBJECT_ID, "")
    is_add_indicator = convert_string_to_bool(rowData.get(form_consts.Object.ADD_INDICATOR, "False"))

    all_obj_type_choices = cache.get("object_types")

    if all_obj_type_choices == None:
        all_obj_type_choices = [(c[0],
                c[0],
                {'datatype':c[1].keys()[0],
                 'datatype_value':c[1].values()[0]}
                ) for c in get_object_types(False)]
        cache["object_types"] = all_obj_type_choices

    data = {
        'object_type': object_type,
        'value': value,
        'source': source,
        'method': method,
        'reference': reference,
        'otype': otype,
        'oid': oid,
        'add_indicator': is_add_indicator
    }

    bound_form = cache.get("object_form")

    if bound_form == None:
        bound_form = AddObjectForm(request.user, all_obj_type_choices, data)
        cache['object_form'] = bound_form
    else:
        bound_form.data = data

    bound_form.full_clean()

    return bound_form

