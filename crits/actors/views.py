import json
import urllib

from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.actors.forms import AddActorForm, AddActorIdentifierForm
from crits.actors.handlers import generate_actor_csv, generate_actor_jtable
from crits.actors.handlers import generate_actor_identifier_jtable
from crits.actors.handlers import generate_actor_identifier_csv
from crits.actors.handlers import get_actor_details, add_new_actor, actor_remove
from crits.actors.handlers import create_actor_identifier_type
from crits.actors.handlers import get_actor_tags_by_type, update_actor_tags
from crits.actors.handlers import add_new_actor_identifier, actor_identifier_types
from crits.actors.handlers import actor_identifier_type_values
from crits.actors.handlers import attribute_actor_identifier
from crits.actors.handlers import set_identifier_confidence, remove_attribution
from crits.actors.handlers import set_actor_name
from crits.actors.handlers import update_actor_aliases
from crits.core import form_consts
from crits.core.data_tools import json_handler
from crits.core.user_tools import user_can_view_data, is_admin


@user_passes_test(user_can_view_data)
def actor_identifiers_listing(request,option=None):
    """
    Generate the Actor Identifier listing page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', 'csv', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_actor_identifier_csv(request)
    return generate_actor_identifier_jtable(request, option)

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
                                content_type="application/json")
        return HttpResponse(json.dumps({'success': False,
                                        'form':form.as_table()}),
                            content_type="application/json")
    return render_to_response("error.html",
                              {'error': 'Expected AJAX/POST'},
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def remove_actor(request, id_):
    """
    Remove an Actor.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param id_: The ObjectId of the Actor to remove.
    :type id_: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST":
        if is_admin(request.user):
            actor_remove(id_, request.user.username)
            return HttpResponseRedirect(reverse('crits.actors.views.actors_listing'))
        error = 'You do not have permission to remove this item.'
        return render_to_response("error.html",
                                  {'error': error},
                                  RequestContext(request))
    return render_to_response('error.html',
                              {'error':'Expected AJAX/POST'},
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def get_actor_identifier_types(request):
    """
    Get Actor Identifier types. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        result = actor_identifier_types(True)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def get_actor_identifier_type_values(request):
    """
    Get Actor Identifier type values. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        type_ = request.POST.get('type', None)
        username = request.user.username
        result = actor_identifier_type_values(type_, username)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
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
                                content_type="application/json")
        result = create_actor_identifier_type(username, identifier_type)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def actor_tags_modify(request):
    """
    Update tags for Actors based on a type of tag.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        tag_type = request.POST.get('tag_type', None)
        id_ = request.POST.get('oid', None)
        tags = request.POST.get('tags', None)
        user = request.user.username
        if not tag_type:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Need a tag type.'}),
                                content_type="application/json")
        result = update_actor_tags(id_, tag_type, tags, user)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def get_actor_tags(request):
    """
    Get available tags for Actors based on a type of tag.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        tag_type = request.POST.get('type', None)
        if not tag_type:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Need a tag type.'}),
                                content_type="application/json")
        result = get_actor_tags_by_type(tag_type)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def add_identifier(request):
    """
    Create an Actor Identifier. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        username = request.user.username
        form = AddActorIdentifierForm(username, request.POST)
        if form.is_valid():
            identifier_type = request.POST.get('identifier_type', None)
            identifier = request.POST.get('identifier', None)
            source = request.POST.get('source', None)
            method = request.POST.get('method', None)
            reference = request.POST.get('reference', None)
            if not identifier_type or not identifier:
                return HttpResponse(json.dumps({'success': False,
                                                'message': 'Need a name.'}),
                                    content_type="application/json")
            result = add_new_actor_identifier(identifier_type,
                                              identifier,
                                              source,
                                              method,
                                              reference,
                                              username)
            return HttpResponse(json.dumps(result),
                                content_type="application/json")
        else:
            return HttpResponse(json.dumps({'success': False,
                                            'form':form.as_table()}),
                                content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def attribute_identifier(request):
    """
    Attribute an Actor Identifier. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        user = request.user.username
        id_ = request.POST.get('id', None)
        identifier_type = request.POST.get('identifier_type', None)
        identifier = request.POST.get('identifier', None)
        confidence = request.POST.get('confidence', 'low')
        if not identifier_type or not identifier:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Not all info provided.'}),
                                content_type="application/json")
        result = attribute_actor_identifier(id_,
                                            identifier_type,
                                            identifier,
                                            confidence,
                                            user)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def edit_attributed_identifier(request):
    """
    Edit an attributed Identifier (change confidence). Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        user = request.user.username
        id_ = request.POST.get('id', None)
        identifier = request.POST.get('identifier_id', None)
        confidence = request.POST.get('confidence', 'low')
        if not identifier:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Not all info provided.'}),
                                content_type="application/json")
        result = set_identifier_confidence(id_,
                                           identifier,
                                           confidence,
                                           user)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def remove_attributed_identifier(request):
    """
    Remove an Identifier attribution. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        user = request.user.username
        id_ = request.POST.get('object_type', None)
        identifier = request.POST.get('key', None)
        if not identifier:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Not all info provided.'}),
                                content_type="application/json")
        result = remove_attribution(id_,
                                    identifier,
                                    user)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def edit_actor_name(request, id_):
    """
    Set actor name. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param id_: The ObjectId of the Actor.
    :type id_: str
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        user = request.user.username
        name = request.POST.get('name', None)
        if not name:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Not all info provided.'}),
                                content_type="application/json")
        result = set_actor_name(id_,
                                name,
                                user)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def edit_actor_aliases(request):
    """
    Update aliases for an Actor.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        aliases = request.POST.get('aliases', None)
        id_ = request.POST.get('oid', None)
        user = request.user.username
        result = update_actor_aliases(id_, aliases, user)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))
