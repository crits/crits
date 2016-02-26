import json

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test

from crits.locations.forms import AddLocationForm
from crits.locations.handlers import (
    location_add,
    location_remove,
    get_location_names_list,
    location_edit
)
from crits.core.user_tools import user_can_view_data


@user_passes_test(user_can_view_data)
def location_names(request, active_only=True):
    """
    Generate Location name list.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param active_only: Whether we return active locations only (default)
    :type active_only: str
    :returns: :class:`django.http.HttpResponse`
    """

    location_list = get_location_names_list(active_only)
    return HttpResponse(json.dumps(location_list), content_type="application/json")

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
                                    content_type="application/json")
        result['form'] = form.as_table()
        result['success'] = False
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        return HttpResponse(json.dumps({'success': False,
                                        'message': "Expected AJAX request."}),
                            content_type="application/json")

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
        date = data.get('key').split('|')[2]
        result = location_remove(id_,
                                 type_,
                                 location_name=location_name,
                                 location_type=location_type,
                                 date=date,
                                 user=request.user.username)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        return render_to_response("error.html",
                                  {"error": 'Expected AJAX POST.'},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def edit_location(request, type_, id_):
    """
    Edit a location. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        location_type = request.POST.get('location_type', None)
        location_name = request.POST.get('location_name', None)
        date = request.POST.get('date', None)
        description = request.POST.get('description', None)
        latitude = request.POST.get('latitude', None)
        longitude = request.POST.get('longitude', None)
        user = request.user.username
        return HttpResponse(json.dumps(location_edit(type_,
                                                     id_,
                                                     location_name,
                                                     location_type,
                                                     date,
                                                     user,
                                                     description=description,
                                                     latitude=latitude,
                                                     longitude=longitude)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error": error},
                                  RequestContext(request))
