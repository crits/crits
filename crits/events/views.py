from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
import json
import urllib.request, urllib.parse, urllib.error

from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.core import form_consts
from crits.core.user_tools import user_can_view_data, user_is_admin
from crits.events.forms import EventForm
from crits.events.handlers import event_remove
from crits.events.handlers import update_event_title, update_event_type
from crits.events.handlers import get_event_details
from crits.events.handlers import generate_event_jtable, add_sample_for_event
from crits.events.handlers import generate_event_csv, add_new_event
from crits.samples.forms import UploadFileForm

from crits.vocabulary.events import EventTypes


@user_passes_test(user_can_view_data)
def events_listing(request, option=None):
    """
    Generate Event Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_event_csv(request)
    return generate_event_jtable(request, option)


@user_passes_test(user_can_view_data)
def add_event(request):
    """
    Add an event to CRITs. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        event_form = EventForm(request.user, request.POST)
        if event_form.is_valid():
            data = event_form.cleaned_data
            result = add_new_event(title=data['title'],
                                   description=data['description'],
                                   event_type=data['event_type'],
                                   source=data['source'],
                                   method=data['method'],
                                   reference=data['reference'],
                                   date=data['occurrence_date'],
                                   bucket_list=data[form_consts.Common.BUCKET_LIST_VARIABLE_NAME],
                                   ticket=data[form_consts.Common.TICKET_VARIABLE_NAME],
                                   campaign=data['campaign'],
                                   campaign_confidence=data['campaign_confidence'],
                                   analyst=request.user.username,
                                   related_id=data['related_id'],
                                   related_type=data['related_type'],
                                   relationship_type=data['relationship_type'])
            if 'object' in result:
                del result['object']
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            return HttpResponse(json.dumps({'form': event_form.as_table(),
                                            'success': False}),
                                content_type="application/json")
    else:
        return render_to_response("error.html",
                                  {"error": "Expected AJAX POST"},
                                  RequestContext(request))


@user_passes_test(user_can_view_data)
def event_search(request):
    """
    Search for events.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    query = {}
    query[request.GET.get('search_type', '')] = request.GET.get('q', '').strip()
    return HttpResponseRedirect(reverse('crits.events.views.events_listing') +
                                "?%s" % urllib.parse.urlencode(query))


@user_passes_test(user_can_view_data)
def view_event(request, eventid):
    """
    View an Event.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param eventid: The ObjectId of the event to get details for.
    :type eventid: str
    :returns: :class:`django.http.HttpResponse`
    """

    analyst = request.user.username
    template = 'event_detail.html'
    (new_template, args) = get_event_details(eventid, analyst)
    if new_template:
        template = new_template
    return render_to_response(template,
                              args,
                              RequestContext(request))


@user_passes_test(user_is_admin)
def remove_event(request, _id):
    """
    Remove an Event.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the event to remove.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`, :class:`django.http.HttpResponse`
    """

    result = event_remove(_id, '%s' % request.user.username)
    if result['success']:
        return HttpResponseRedirect(
            reverse('crits.events.views.events_listing')
        )
    else:
        return render_to_response('error.html',
                                  {'error': result['message']},
                                  RequestContext(request))


@user_passes_test(user_can_view_data)
def set_event_title(request, event_id):
    """
    Set event title. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param event_id: The ObjectId of the event to update.
    :type event_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        analyst = request.user.username
        title = request.POST.get('title', None)
        return HttpResponse(json.dumps(update_event_title(event_id,
                                                          title,
                                                          analyst)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error": error},
                                  RequestContext(request))


@user_passes_test(user_can_view_data)
def set_event_type(request, event_id):
    """
    Set event type. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param event_id: The ObjectId of the event to update.
    :type event_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        analyst = request.user.username
        event_type = request.POST.get('type', None)
        return HttpResponse(json.dumps(update_event_type(event_id,
                                                         event_type,
                                                         analyst)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error": error},
                                  RequestContext(request))


@user_passes_test(user_can_view_data)
def get_event_type_dropdown(request):
    """
    Get a list of available event types.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.is_ajax():
        e_types = EventTypes.values(sort=True)
        result = {'types': e_types}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX"
        return render_to_response("error.html",
                                    {"error": error},
                                    RequestContext(request))
