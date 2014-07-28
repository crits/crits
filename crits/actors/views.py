import json
import urllib

from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.actors.forms import AddActorForm
from crits.actors.handlers import generate_actor_csv, generate_actor_jtable
from crits.actors.handlers import get_actor_details, add_new_actor, actor_remove
from crits.actors.handlers import create_actor_identifier_type
from crits.core import form_consts
from crits.core.data_tools import json_handler
from crits.core.user_tools import user_can_view_data, is_admin


@user_passes_test(user_can_view_data)
def actors_listing(request,option=None):
    """
    Generate the Actor listing page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', 'csv', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_actor_csv(request)
    return generate_actor_jtable(request, option)

@user_passes_test(user_can_view_data)
def actor_search(request):
    """
    Search for Actors.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    query = {}
    query[request.GET.get('search_type', '')]=request.GET.get('q', '').strip()
    return HttpResponseRedirect(reverse('crits.actors.views.actors_listing')
                                + "?%s" % urllib.urlencode(query))

@user_passes_test(user_can_view_data)
def actor_detail(request, id_):
    """
    Generate the Actor details page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param id_: The Actor ObjectId to get details for.
    :type id_: str
    :returns: :class:`django.http.HttpResponse`
    """

    template = "actor_detail.html"
    analyst = request.user.username
    (new_template, args) = get_actor_details(id_,
                                             analyst)
    if new_template:
        template = new_template
    return render_to_response(template,
                              args,
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def add_actor(request):
    """
    Add an Actor. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        data = request.POST
        form = AddActorForm(request.user, data)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            name = cleaned_data['name']
            aliases = cleaned_data['aliases']
            description = cleaned_data['description']
            source = cleaned_data['source']
            reference = cleaned_data['source_reference']
            method = cleaned_data['source_method']
            campaign = cleaned_data['campaign']
            confidence = cleaned_data['confidence']
            analyst = request.user.username
            bucket_list = cleaned_data.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
            ticket = cleaned_data.get(form_consts.Common.TICKET_VARIABLE_NAME)

            result = add_new_actor(name,
                                   aliases=aliases,
                                   description=description,
                                   source=source,
                                   source_method=method,
                                   source_reference=reference,
                                   campaign=campaign,
                                   confidence=confidence,
                                   analyst=analyst,
                                   bucket_list=bucket_list,
                                   ticket=ticket)
            return HttpResponse(json.dumps(result,
                                           default=json_handler),
                                mimetype='application/json')
        return HttpResponse(json.dumps({'success': False,
                                        'form':form.as_table()}),
                            mimetype="application/json")
    return render_to_response("error.html",
                              {'error': 'Expected AJAX/POST'},
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def remove_actor(request):
    """
    Remove an Actor. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        if is_admin(request.user):
            result = actor_remove(request.POST['key'],
                               request.user.username)
            return HttpResponse(json.dumps(result),
                                mimetype="application/json")
        error = 'You do not have permission to remove this item.'
        return render_to_response("error.html",
                                  {'error': error},
                                  RequestContext(request))
    return render_to_response('error.html',
                              {'error':'Expected AJAX/POST'},
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def new_actor_identifier_type(request):
    """
    Create an Actor Identifier type. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        username = request.user.username
        identifier_type = request.POST.get('identifier_type', None)
        if not identifier_type:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Need a name.'}),
                                mimetype="application/json")
        result = create_actor_identifier_type(username, identifier_type)
        return HttpResponse(json.dumps(result),
                            mimetype="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))
