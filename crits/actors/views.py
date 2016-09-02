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
from crits.core.user_tools import user_can_view_data

from crits.vocabulary.acls import ActorACL

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

    request.user._setup()
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

    request.user._setup()
    user = request.user

    if user.has_access_to(ActorACL.READ):
        if option == "csv":
            return generate_actor_csv(request)
        return generate_actor_jtable(request, option)
    else:
        return render_to_response("error.html",
                                  {'error': 'User does not have permission to view actor listing.'},
                                  RequestContext(request))

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
    request.user._setup()
    user = request.user

    if user.has_access_to(ActorACL.READ):
        (new_template, args) = get_actor_details(id_,
                                                 request.user)
        if new_template:
            template = new_template

        return render_to_response(template,
                                  args,
                                  RequestContext(request))

    else:
        return render_to_response("error.html",
                                  {'error': 'User does not have permission to view actor details.'},
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
        request.user._setup()
        user = request.user
        data = request.POST
        form = AddActorForm(request.user.username, data)
        if form.is_valid():
            if user.has_access_to(ActorACL.WRITE):
                cleaned_data = form.cleaned_data
                name = cleaned_data['name']
                aliases = cleaned_data['aliases']
                description = cleaned_data['description']
                source = cleaned_data['source_name']
                reference = cleaned_data['source_reference']
                method = cleaned_data['source_method']
                tlp = cleaned_data['source_tlp']
                campaign = cleaned_data['campaign']
                confidence = cleaned_data['confidence']
                bucket_list = cleaned_data.get(
                    form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
                ticket = cleaned_data.get(form_consts.Common.TICKET_VARIABLE_NAME)
                related_id = cleaned_data['related_id']
                related_type = cleaned_data['related_type']
                relationship_type = cleaned_data['relationship_type']

                result = add_new_actor(name,
                                       aliases=aliases,
                                       description=description,
                                       source=source,
                                       source_method=method,
                                       source_reference=reference,
                                       source_tlp=tlp,
                                       campaign=campaign,
                                       confidence=confidence,
                                       user=user,
                                       bucket_list=bucket_list,
                                       ticket=ticket,
                                       related_id=related_id,
                                       related_type=related_type,
                                       relationship_type=relationship_type)
            else:
                result = {"success":False,
                          "message":"User does not have permission to add Actors."}

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

    request.user._setup()
    user = request.user
    if request.method == "POST":
        if user.has_access_to(ActorACL.DELETE):
            actor_remove(id_, request.user)
            return HttpResponseRedirect(reverse('crits.actors.views.actors_listing'))
        else:
            return render_to_response('error.html',
                                      {'error':'User does not have permission to remove actor.'},
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
        request.user._setup()
        type_ = request.POST.get('type', None)
        result = actor_identifier_type_values(type_, request.user)
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
        request.user._setup()
        user = request.user
        identifier_type = request.POST.get('identifier_type', None)

        if not identifier_type:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Need a name.'}),
                                mimetype="application/json")
        if user.has_access_to(ActorACL.ADD_NEW_ACTOR_IDENTIFIER_TYPE):
            result = create_actor_identifier_type(identifier_type, request.user)
        else:
            result = {'message': 'User does not have permission to add actor identifier',
                      'success': False}
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
        request.user._setup()
        user = request.user


        tag_type = request.POST.get('tag_type', None)
        id_ = request.POST.get('oid', None)
        tags = request.POST.get('tags', None)
        if not tag_type:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Need a tag type.'}),
                                mimetype="application/json")

        # Get the appropriate permission to look up
        if tag_type=='ActorMotivation':
            perm_needed=ActorACL.MOTIVATIONS_EDIT
        elif tag_type=='ActorIntendedEffect':
            perm_needed=ActorACL.INTENDED_EFFECTS_EDIT
        elif tag_type=='ActorSophistication':
            perm_needed=ActorACL.SOPHISTICATIONS_EDIT
        elif tag_type=='ActorThreatType':
            perm_needed=ActorACL.THREAT_TYPES_EDIT

        if user.has_access_to(perm_needed):
            result = update_actor_tags(id_, tag_type, tags, request.user)
        else:
            result = {'success':False,
                      'message':'User does not have permssion to modify tag.'}
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
        request.user._setup()
        user = request.user
        form = AddActorIdentifierForm(request.user.username, request.POST)
        if form.is_valid():
            identifier_type = request.POST.get('identifier_type', None)
            identifier = request.POST.get('identifier', None)
            source = request.POST.get('source_name', None)
            method = request.POST.get('source_method', None)
            reference = request.POST.get('source_reference', None)
            tlp = request.POST.get('source_tlp', None)
            if not identifier_type or not identifier:
                return HttpResponse(json.dumps({'success': False,
                                                'message': 'Need a name.'}),
                                    content_type="application/json")
            if user.has_access_to(ActorACL.ACTOR_IDENTIFIERS_ADD):
                result = add_new_actor_identifier(identifier_type,
                                                  identifier,
                                                  source,
                                                  method,
                                                  reference,
                                                  tlp,
                                                  request.user)
            else:
                result = {'success':False,
                          'message':'User does not have permission to add actor identifier.'}
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
        request.user._setup()
        user = request.user

        if user.has_access_to(ActorACL.ACTOR_IDENTIFIERS_ADD):
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
                                                request.user)
        else:
            result = {'success': False,
                      'message': 'User does not have permission to attribute actor identifier.' }
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
        request.user._setup()
        user = request.user
        id_ = request.POST.get('id', None)
        identifier = request.POST.get('identifier_id', None)
        confidence = request.POST.get('confidence', 'low')
        if not identifier:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Not all info provided.'}),
                                content_type="application/json")
        if user.has_access_to(ActorACL.ACTOR_IDENTIFIERS_EDIT):
            result = set_identifier_confidence(id_,
                                               identifier,
                                               confidence,
                                               request.user)
        else:
            result = {"success":False,
                      "message":"User does not have permission to edit identifiers."}
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
        request.user._setup()
        user = request.user

        id_ = request.POST.get('object_type', None)
        identifier = request.POST.get('key', None)
        if not identifier:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Not all info provided.'}),
                                content_type="application/json")
        if user.has_access_to(ActorACL.ACTOR_IDENTIFIERS_DELETE):
            result = remove_attribution(id_,
                                        identifier,
                                        request.user)
        else:
            result = {"success":False,
                      "message":"User does not have permission to remove attributed identifer."}
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
        request.user._setup()
        user = request.user
        if user.has_access_to(ActorACL.NAME_EDIT):
            name = request.POST.get('name', None)
            if not name:
                return HttpResponse(json.dumps({'success': False,
                                                'message': 'Not all info provided.'}),
                                    content_type="application/json")
            result = set_actor_name(id_,
                                    name,
                                    request.user)
        else:
            result = {'success':False,
                      'message':'User does not have permission to edit name.'}
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
        request.user._setup()
        user = request.user
        aliases = request.POST.get('aliases', None)
        id_ = request.POST.get('oid', None)
        if user.has_access_to(ActorACL.ALIASES_EDIT):
            result = update_actor_aliases(id_, aliases, request.user)
            return HttpResponse(json.dumps(result),
                                content_type="application/json")
        else:
            return render_to_response("error.html",
                                      {"error" : 'User does not have permission to edit alias.'},
                                      RequestContext(request))
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))
