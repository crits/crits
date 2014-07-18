import json

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext

from crits.core.form_consts import get_source_field_for_class
from crits.core.class_mapper import class_from_id
from crits.core.data_tools import json_handler
from crits.core.handlers import get_object_types
from crits.objects.handlers import add_object, delete_object
from crits.objects.handlers import update_object_value, update_object_source
from crits.objects.handlers import create_indicator_from_object
from crits.objects.handlers import parse_row_to_bound_object_form, add_new_handler_object_via_bulk
from crits.objects.forms import AddObjectForm
from crits.core.handsontable_tools import form_to_dict, parse_bulk_upload, get_field_from_label
from crits.core.user_tools import user_can_view_data

@user_passes_test(user_can_view_data)
def add_new_object(request):
    """
    Add a new object.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        analyst = "%s" % request.user
        result = ""
        message = ""
        my_type = request.POST['otype']
        all_obj_type_choices = [(c[0],
                                 c[0],
                                 {'datatype':c[1].keys()[0],
                                  'datatype_value':c[1].values()[0]}
                                 ) for c in get_object_types(False)]
        form = AddObjectForm(analyst,
                             all_obj_type_choices,
                             request.POST,
                             request.FILES)
        if not form.is_valid() and not 'value' in request.FILES:
            message = "Invalid Form: %s" % form.errors
            form = form.as_table()
            response = json.dumps({'message': message,
                                   'form': form,
                                   'success': False})
            if request.is_ajax():
                return HttpResponse(response, mimetype="application/json")
            else:
                return render_to_response("file_upload_response.html",
                                          {'response':response},
                                          RequestContext(request))
        source = request.POST['source']
        oid = request.POST['oid']
        ot_array = request.POST['object_type'].split(" - ")
        object_type = ot_array[0]
        name = ot_array[1] if len(ot_array) == 2 else ot_array[0]
        method = request.POST['method']
        reference = request.POST['reference']
        add_indicator = request.POST.get('add_indicator', None)
        data = None
        # if it was a file upload, handle the file appropriately
        if 'value' in request.FILES:
            data = request.FILES['value']
        value = request.POST.get('value', None)
        if isinstance(value, basestring):
            value = value.strip()
        results = add_object(my_type,
                             oid,
                             object_type,
                             name,
                             source,
                             method,
                             reference,
                             analyst,
                             value=value,
                             file_=data,
                             add_indicator=add_indicator,
                             is_sort_relationships=True)
        if results['success']:
            subscription = {
                'type': my_type,
                'id': oid
            }

            if results.get('relationships', None):
                relationship = {'type': my_type,
                                'value': oid}
                relationships = results['relationships']

                html = render_to_string('objects_listing_widget.html',
                                        {'objects': results['objects'],
                                         'relationships': relationships,
                                         'subscription': subscription},
                                        RequestContext(request))
                result = {'success': True,
                          'html': html,
                          'message': results['message']}

                rel_msg  = render_to_string('relationships_listing_widget.html',
                                            {'relationship': relationship,
                                             'nohide': True,
                                             'relationships': relationships},
                                            RequestContext(request))
                result['rel_made'] = True
                result['rel_msg'] = rel_msg
            else:
                html = render_to_string('objects_listing_widget.html',
                                        {'objects': results['objects'],
                                         'subscription': subscription},
                                        RequestContext(request))
                result = {'success': True,
                          'html': html,
                          'message': results['message']}
        else:
            message = "Error adding object: %s" % results['message']
            result = {'success': False, 'message': message}
        if request.is_ajax():
            return HttpResponse(json.dumps(result),
                                mimetype="application/json")
        else:
            return render_to_response("file_upload_response.html",
                                      {'response': json.dumps(result)},
                                      RequestContext(request))
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def bulk_add_object(request):
    """
    Bulk add objects.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    all_obj_type_choices = [(c[0],
                            c[0],
                            {'datatype':c[1].keys()[0],
                            'datatype_value':c[1].values()[0]}
                            ) for c in get_object_types(False, query={'datatype.file':{'$exists':0}})]

    formdict = form_to_dict(AddObjectForm(request.user, all_obj_type_choices))

    if request.method == "POST" and request.is_ajax():
        response = parse_bulk_upload(request, parse_row_to_bound_object_form, add_new_handler_object_via_bulk, formdict)

        return HttpResponse(json.dumps(response,
                            default=json_handler),
                            mimetype='application/json')
    else:
        return render_to_response('bulk_add_default.html',
                                  {'formdict': formdict,
                                  'title': "Bulk Add Objects",
                                  'table_name': 'object'},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def bulk_add_object_inline(request):
    """
    Bulk add objects inline.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """
    all_obj_type_choices = [(c[0], c[0], {'datatype':c[1].keys()[0],
                            'datatype_value':c[1].values()[0]}
                            ) for c in get_object_types(False, query={'datatype.file':{'$exists':0}})]

    formdict = form_to_dict(AddObjectForm(request.user, all_obj_type_choices))

    if request.method == "POST" and request.is_ajax():
        response = parse_bulk_upload(request, parse_row_to_bound_object_form, add_new_handler_object_via_bulk, formdict)

        secondary_data_array = response.get('secondary')
        if secondary_data_array:
            latest_secondary_data = secondary_data_array[-1]
            class_type = class_from_id(latest_secondary_data['type'], latest_secondary_data['id'])

            subscription = {'type': latest_secondary_data['type'],
                            'id': latest_secondary_data['id'],
                            'value': latest_secondary_data['id']}

            object_listing_html = render_to_string('objects_listing_widget.html',
                                                   {'objects': class_type.sort_objects(),
                                                    'subscription': subscription},
                                                   RequestContext(request))

            response['html'] = object_listing_html

            is_relationship_made = False
            for secondary_data in secondary_data_array:
                if secondary_data.get('relationships'):
                    is_relationship_made = True
                    break

            if is_relationship_made == True:
                rel_html = render_to_string('relationships_listing_widget.html',
                                            {'relationship': subscription,
                                             'relationships': class_type.sort_relationships(request.user, meta=True)},
                                            RequestContext(request))

                response['rel_msg'] = rel_html
                response['rel_made'] = True

        return HttpResponse(json.dumps(response,
                            default=json_handler),
                            mimetype='application/json')
    else:
        is_prevent_initial_table = request.GET.get('isPreventInitialTable', False)
        is_use_item_source = request.GET.get('useItemSource', False)

        if is_use_item_source == True or is_use_item_source == "true":
            otype = request.GET.get('otype')
            oid = request.GET.get('oid')

            # Get the item with the type and ID from the database
            obj = class_from_id(otype, oid)


            if obj:
                source_field_name = get_source_field_for_class(otype)
                if source_field_name:

                    # If the item has a source, then use the source value
                    # to set as the default source
                    if hasattr(obj, "source"):
                        source_field = get_field_from_label("source", formdict)
                        earliest_source = None
                        earliest_date = None

                        # Get the earliest source, compared by date
                        for source in obj.source:
                            for source_instance in source.instances:
                                if earliest_source == None or source_instance.date < earliest_date:
                                    earliest_date = source_instance.date
                                    earliest_source = source

                        if earliest_source:
                            source_field['initial'] = earliest_source.name

        return render_to_response('bulk_add_object_inline.html',
                                  {'formdict': formdict,
                                   'title': "Bulk Add Objects",
                                   'is_prevent_initial_table': is_prevent_initial_table,
                                   'table_name': 'object_inline'},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def update_objects_value(request):
    """
    Update an object's value. Should be an AJAX POST.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        type_ = request.POST['coll']
        oid = request.POST['oid']
        name = request.POST.get('name')
        object_type = request.POST.get('type')
        value = request.POST['value']
        new_value = request.POST['new_value']
        analyst = "%s" % request.user.username
        results = update_object_value(type_,
                                      oid,
                                      object_type,
                                      name,
                                      value,
                                      new_value,
                                      analyst)
        if results['success']:
            message = "Successfully updated object value: %s" % results['message']
            result = {'success': True, 'message': message}
        else:
            message = "Error updating object value: %s" % results['message']
            result = {'success': False, 'message': message}
        return HttpResponse(json.dumps(result), mimetype="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def update_objects_source(request):
    """
    Update an object's source. Should be an AJAX POST.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        type_ = request.POST['coll']
        oid = request.POST['oid']
        name = request.POST.get('name')
        object_type = request.POST.get('type')
        value = request.POST['value']
        new_source = request.POST['new_source']
        new_method = request.POST['new_method']
        new_reference = request.POST['new_reference']
        analyst = "%s" % request.user.username
        results = update_object_source(type_,
                                       oid,
                                       object_type,
                                       name,
                                       value,
                                       new_source,
                                       new_method,
                                       new_reference,
                                       analyst)
        if results['success']:
            message = "Successfully updated object source: %s" % results['message']
            result = {'success': True, 'message': message}
        else:
            message = "Error updating object source: %s" % results['message']
            result = {'success': False, 'message': message}
        return HttpResponse(json.dumps(result),
                            mimetype="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def get_object_type_dropdown(request):
    """
    Get the list of object types for UI dropdowns. Should be an AJAX POST.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    # NOTE: query is no longer a free-form ajax object that is passed onto mongo
    # There was a Mongo Injection issue here before. get_object_types
    # query is passed into mongo as a raw WHERE clause, permitting
    # javascript injection into mongo.
    # Only searches seen used so far is {datatype.file:{$exists:0}}, so this was changed around to
    # only look for a query:'no_file' and sets the where clause for the handler to remove the
    # exposure here

    if request.method == 'POST' and request.is_ajax():
        dd_types = ""
        query = {}
        if 'query' in request.POST and request.POST['query'] != "":
            if request.POST['query'] == "no_file":
                query = {'datatype.file':{'$exists':0}}
            else:
                message = "Invalid Query passed"
                result = {'success': False, 'message': message}
                return HttpResponse(json.dumps(result),
                                    mimetype="application/json")

        if 'all' in request.POST:
            dd_types = get_object_types(False, query)
        else:
            dd_types = get_object_types(True, query)
        dd_final = {}
        for obj_type in dd_types:
            dd_final[obj_type[0]] = obj_type
        result = {'types': dd_final}
        return HttpResponse(json.dumps(result),
                            mimetype="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def delete_this_object(request):
    """
    Delete an object. Should be an AJAX POST.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    error = ""
    if request.method == 'POST':
        if request.is_ajax():
            type_ = request.POST['coll']
            oid = request.POST['oid']
            analyst = "%s" % request.user
            result = ""
            message = ""
            object_type = request.POST.get('object_type')
            name = request.POST.get('name')
            value = request.POST['value']
            results = delete_object(type_,
                                    oid,
                                    object_type,
                                    name,
                                    value,
                                    analyst)
            if results['success']:
                message = results['message']
                result = {'success': True, 'message': message}
            else:
                message = "Error deleting object: %s" % results['message']
                result = {'success': False, 'message': message}
            return HttpResponse(json.dumps(result),
                                mimetype="application/json")
        else:
            error = "Expected AJAX"
    else:
        error = "Expected POST"
    return render_to_response("error.html",
                              {"error" : error },
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def indicator_from_object(request):
    """
    Create an indicator out of an object. Should be an AJAX POST.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        rel_type = request.POST.get('rel_type', None)
        rel_id = request.POST.get('rel_id', None)
        ind_type = request.POST.get('ind_type', None)
        value = request.POST.get('value', None)
        analyst = "%s" % request.user.username
        result = create_indicator_from_object(rel_type,
                                              rel_id,
                                              ind_type,
                                              value,
                                              analyst,
                                              request)
        return HttpResponse(json.dumps(result),
                            mimetype="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))
