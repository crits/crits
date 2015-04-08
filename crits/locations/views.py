import json

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test

from crits.locations.forms import AddLocationForm
from crits.locations.handlers import location_add, location_remove
from crits.core.user_tools import user_can_view_data


@user_passes_test(user_can_view_data)
def add_location(request, type_, id_):
    """
    Attribute a location to a top-level object. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param type_: CRITs type for the top-level object.
    :type type_: str
    :param id_: The ObjectId of the top-level object.
    :type id_: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        form = AddLocationForm(request.POST)
        result = {}
        if form.is_valid():
            data = form.cleaned_data
            location_type = data['location_type']
            location_name = data['country']
            description = data['description']
            latitude = data['latitude']
            longitude = data['longitude']
            user = request.user.username
            result = location_add(id_,
                                  type_,
                                  location_type,
                                  location_name,
                                  user,
                                  description=description,
                                  latitude=latitude,
                                  longitude=longitude)
            if result['success']:
                return HttpResponse(json.dumps(result),
                                    mimetype="application/json")
        result['form'] = form.as_table()
        result['success'] = False
        return HttpResponse(json.dumps(result),
                            mimetype="application/json")
    else:
        return HttpResponse(json.dumps({'success': False,
                                        'message': "Expected AJAX request."}),
                            mimetype="application/json")

@user_passes_test(user_can_view_data)
def remove_location(request, type_, id_):
    """
    Remove an attributed location from a top-level object. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param type_: CRITs type for the top-level object.
    :type type_: str
    :param id_: The ObjectId of the top-level object.
    :type id_: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        data = request.POST
        location_name = data.get('key').split('|')[0]
        location_type = data.get('key').split('|')[1]
        result = location_remove(id_,
                                 type_,
                                 location_name=location_name,
                                 location_type=location_type,
                                 user=request.user.username)
        return HttpResponse(json.dumps(result), mimetype="application/json")
    else:
        return render_to_response("error.html",
                                  {"error": 'Expected AJAX POST.'},
                                  RequestContext(request))
