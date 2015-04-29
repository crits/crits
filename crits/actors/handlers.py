import json

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string

from crits.actors.actor import Actor, ActorIdentifier, ActorThreatIdentifier
from crits.core.class_mapper import class_from_type
from crits.core.crits_mongoengine import EmbeddedCampaign, json_handler
from crits.core.crits_mongoengine import create_embedded_source
from crits.core.forms import DownloadFileForm
from crits.core.handlers import build_jtable, jtable_ajax_list, jtable_ajax_delete
from crits.core.handlers import csv_export
from crits.core.user_tools import is_admin, is_user_subscribed, user_sources
from crits.core.user_tools import is_user_favorite
from crits.notifications.handlers import remove_user_from_notification
from crits.services.handlers import run_triage, get_supported_services

def generate_actor_identifier_csv(request):
    """
    Generate a CSV file of the Actor Identifier information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request, ActorIdentifier)
    return response

def generate_actor_csv(request):
    """
    Generate a CSV file of the Actor information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request, Actor)
    return response

def generate_actor_identifier_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = ActorIdentifier
    type_ = "actor_identifier"
    mapper = obj_type._meta['jtable_opts']
    if option == "jtlist":
        # Sets display url
        details_url = mapper['details_url']
        details_url_key = mapper['details_url_key']
        fields = mapper['fields']
        response = jtable_ajax_list(obj_type,
                                    details_url,
                                    details_url_key,
                                    request,
                                    includes=fields)
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    if option == "jtdelete":
        response = {"Result": "ERROR"}
        if jtable_ajax_delete(obj_type, request):
            obj_id = request.POST.get('id', None)
            if obj_id:
                # Remove this identifier from any Actors who reference it.
                Actor.objects(identifiers__identifier_id=obj_id)\
                    .update(pull__identifiers__identifier_id=obj_id)
            response = {"Result": "OK"}
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    jtopts = {
        'title': "Actor Identifiers",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits.actors.views.%ss_listing' %
                           (type_), args=('jtlist',)),
        'deleteurl': reverse('crits.actors.views.%ss_listing' %
                             (type_), args=('jtdelete',)),
        'searchurl': reverse(mapper['searchurl']),
        'fields': mapper['jtopts_fields'],
        'hidden_fields': mapper['hidden_fields'],
        'linked_fields': mapper['linked_fields'],
        'details_link': mapper['details_link'],
        'no_sort': mapper['no_sort']
    }
    jtable = build_jtable(jtopts, request)
    for field in jtable['fields']:
        if field['fieldname'] == "'name'":
            url = reverse('crits.actors.views.actors_listing')
            field['display'] = """ function (data) {
            return '<a href="%s?q='+data.record.id+'&search_type=actor_identifier&force_full=1">'+data.record.name+'</a>';
            }
            """ % url
        break
    jtable['toolbar'] = [
        {
            'tooltip': "'Add Actor Identifier'",
            'text': "'Add Actor Identifier'",
            'click': "function () {$('#new-actor-identifier').click()}",
        },
    ]
    if option == "inline":
        return render_to_response("jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_,
                                   'button': '%ss_tab' % type_},
                                  RequestContext(request))
    else:
        return render_to_response("%s_listing.html" % type_,
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_},
                                  RequestContext(request))

def generate_actor_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = Actor
    type_ = "actor"
    mapper = obj_type._meta['jtable_opts']
    if option == "jtlist":
        # Sets display url
        details_url = mapper['details_url']
        details_url_key = mapper['details_url_key']
        fields = mapper['fields']
        response = jtable_ajax_list(obj_type,
                                    details_url,
                                    details_url_key,
                                    request,
                                    includes=fields)
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    if option == "jtdelete":
        response = {"Result": "ERROR"}
        if jtable_ajax_delete(obj_type, request):
            response = {"Result": "OK"}
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    jtopts = {
        'title': "Actors",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits.%ss.views.%ss_listing' %
                           (type_, type_), args=('jtlist',)),
        'deleteurl': reverse('crits.%ss.views.%ss_listing' %
                             (type_, type_), args=('jtdelete',)),
        'searchurl': reverse(mapper['searchurl']),
        'fields': mapper['jtopts_fields'],
        'hidden_fields': mapper['hidden_fields'],
        'linked_fields': mapper['linked_fields'],
        'details_link': mapper['details_link'],
        'no_sort': mapper['no_sort']
    }
    jtable = build_jtable(jtopts, request)
    jtable['toolbar'] = [
        {
            'tooltip': "'Add Actor'",
            'text': "'Add Actor'",
            'click': "function () {$('#new-actor').click()}",
        },
    ]
    if option == "inline":
        return render_to_response("jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_,
                                   'button': '%ss_tab' % type_},
                                  RequestContext(request))
    else:
        return render_to_response("%s_listing.html" % type_,
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_},
                                  RequestContext(request))

def get_actor_details(id_, analyst):
    """
    Generate the data to render the Actor details template.

    :param id_: The Actor ObjectId to get details for.
    :type actorip: str
    :param analyst: The user requesting this information.
    :type analyst: str
    :returns: template (str), arguments (dict)
    """

    allowed_sources = user_sources(analyst)
    actor = Actor.objects(id=id_, source__name__in=allowed_sources).first()
    template = None
    args = {}
    if not actor:
        template = "error.html"
        error = ('Either no data exists for this Actor or you do not have'
                 ' permission to view it.')
        args = {'error': error}
    else:
        actor.sanitize("%s" % analyst)

        # remove pending notifications for user
        remove_user_from_notification("%s" % analyst, actor.id, 'Actor')

        download_form = DownloadFileForm(initial={"obj_type": 'Actor',
                                                  "obj_id": actor.id})

        # generate identifiers
        actor_identifiers = actor.generate_identifiers_list(analyst)

        # subscription
        subscription = {
            'type': 'Actor',
            'id': actor.id,
            'subscribed': is_user_subscribed("%s" % analyst, 'Actor', actor.id),
        }

        #objects
        objects = actor.sort_objects()

        #relationships
        relationships = actor.sort_relationships("%s" % analyst, meta=True)

        # relationship
        relationship = {
            'type': 'Actor',
            'value': actor.id
        }

        #comments
        comments = {'comments': actor.get_comments(),
                    'url_key': actor.id}

        #screenshots
        screenshots = actor.get_screenshots(analyst)

        # favorites
        favorite = is_user_favorite("%s" % analyst, 'Actor', actor.id)

        # services
        service_list = get_supported_services('Actor')

        # analysis results
        service_results = actor.get_analysis_results()

        args = {'actor_identifiers': actor_identifiers,
                'objects': objects,
                'download_form': download_form,
                'relationships': relationships,
                'relationship': relationship,
                'subscription': subscription,
                'favorite': favorite,
                'service_list': service_list,
                'service_results': service_results,
                'screenshots': screenshots,
                'actor': actor,
                'actor_id': id_,
                'comments': comments}
    return template, args

def get_actor_by_name(allowed_sources, actor):
    """
    Get an Actor from the database by name.

    :param allowed_sources: The sources this Actor is allowed to have.
    :type allowed_sources: list
    :param actor: The Actor address to find.
    :type actor: str
    :returns: :class:`crits.actors.actor.Actor`
    """

    actor = Actor.objects(name=actor, source__name__in=allowed_sources).first()
    return actor

def add_new_actor(name, aliases=None, description=None, source=None,
                  source_method='', source_reference='', campaign=None,
                  confidence=None, analyst=None, bucket_list=None, ticket=None):
    """
    Add an Actor to CRITs.

    :param name: The name of the Actor.
    :type name: str
    :param aliases: Aliases for the actor.
    :type aliases: list or str
    :param description: Description of the actor.
    :type description: str
    :param source: Name of the source which provided this information.
    :type source: str
    :param source_method: Method of acquiring this data.
    :type source_method: str
    :param source_reference: A reference to this data.
    :type source_reference: str
    :param campaign: A campaign to attribute to this actor.
    :type campaign: str
    :param confidence: Confidence level in the campaign attribution.
    :type confidence: str ("low", "medium", "high")
    :param analyst: The user adding this actor.
    :type analyst: str
    :param bucket_list: Buckets to assign to this actor.
    :type bucket_list: str
    :param ticket: Ticket to assign to this actor.
    :type ticket: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
              "object" (if successful) :class:`crits.actors.actor.Actor`
    """

    is_item_new = False
    retVal = {}
    actor = Actor.objects(name=name).first()

    if not actor:
        actor = Actor()
        actor.name = name
        if description:
            actor.description = description.strip()
        is_item_new = True

    if isinstance(source, basestring):
        source = [create_embedded_source(source,
                                         reference=source_reference,
                                         method=source_method,
                                         analyst=analyst)]

    if isinstance(campaign, basestring):
        c = EmbeddedCampaign(name=campaign, confidence=confidence, analyst=analyst)
        campaign = [c]

    if campaign:
        for camp in campaign:
            actor.add_campaign(camp)

    if source:
        for s in source:
            actor.add_source(s)
    else:
        return {"success" : False, "message" : "Missing source information."}

    if not isinstance(aliases, list):
        aliases = aliases.split(',')
        for alias in aliases:
            alias = alias.strip()
            if alias not in actor.aliases:
                actor.aliases.append(alias)

    if bucket_list:
        actor.add_bucket_list(bucket_list, analyst)

    if ticket:
        actor.add_ticket(ticket, analyst)

    actor.save(username=analyst)

    # run actor triage
    if is_item_new:
        actor.reload()
        run_triage(actor, analyst)

    resp_url = reverse('crits.actors.views.actor_detail', args=[actor.id])

    retVal['message'] = ('Success! Click here to view the new Actor: '
                         '<a href="%s">%s</a>' % (resp_url, actor.name))

    retVal['success'] = True
    retVal['object'] = actor
    retVal['id'] = str(actor.id)

    return retVal

def actor_remove(id_, username):
    """
    Remove an Actor from CRITs.

    :param id_: The ObjectId of the Actor to remove.
    :type id_: str
    :param username: The user removing this Actor.
    :type username: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    if is_admin(username):
        actor = Actor.objects(id=id_).first()
        if actor:
            actor.delete(username=username)
            return {'success': True}
        else:
            return {'success': False, 'message': 'Could not find Actor.'}
    else:
        return {'success': False, 'message': 'Must be an admin to remove'}

def create_actor_identifier_type(username, identifier_type):
    """
    Add a new Actor Identifier Type.

    :param username: The CRITs user adding the identifier type.
    :type username: str
    :param identifier_type: The Identifier Type.
    :type identifier_type: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str) if failed.
    """

    identifier = ActorThreatIdentifier.objects(name=identifier_type).first()
    if identifier:
        return {'success': False,
                'message': 'Identifier Type already exists!'}
    else:
        identifier = ActorThreatIdentifier()
        identifier.name = identifier_type
        identifier.save(username=username)
        return {'success': True,
                'message': 'Identifier Type added successfully!'}

def get_actor_tags_by_type(tag_type):
    """
    Get Actor tags based on type. These are tags that could be used for
    attribution.

    :param tag_type: The type of tags to get.
    :type tag_type: str
    :return: list
    """

    tags = []
    if tag_type in ('ActorIntendedEffect',
                    'ActorMotivation',
                    'ActorSophistication',
                    'ActorThreatType'):
        obj = class_from_type(tag_type)
        results = obj.objects()
        tags = [t.name for t in results]
    return tags

def update_actor_tags(id_, tag_type, tags, user, **kwargs):
    """
    Update a subset of tags for an Actor.

    :param id_: The ObjectId of the Actor to update.
    :type id_: str
    :param tag_type: The type of tag we are updating.
    :type tag_type: str
    :param tags: The tags we are setting.
    :type tags: list
    :returns: dict
    """

    actor = Actor.objects(id=id_).first()
    if not actor:
        return {'success': False,
                'message': 'No actor could be found.'}
    else:
        actor.update_tags(tag_type, tags)
        actor.save(username=user)
        return {'success': True}

def add_new_actor_identifier(identifier_type, identifier=None, source=None,
                             source_method='', source_reference='',
                             analyst=None):
    """
    Add an Actor Identifier to CRITs.

    :param identifier_type: The Actor Identifier Type.
    :type identifier_type: str
    :param identifier: The Actor Identifier.
    :type identifier: str
    :param source: Name of the source which provided this information.
    :type source: str
    :param source_method: Method of acquiring this data.
    :type source_method: str
    :param source_reference: A reference to this data.
    :type source_reference: str
    :param analyst: The user adding this actor.
    :type analyst: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
    """

    actor_identifier = ActorIdentifier.objects(identifier_type=identifier_type,
                                               name=identifier).first()

    if not actor_identifier:
        actor_identifier = ActorIdentifier()
        actor_identifier.set_identifier_type(identifier_type)
        if not actor_identifier.identifier_type:
            return {'success': False,
                    'message': "Unknown Identifier Type"}
        if not identifier:
            return {'success': False,
                    'message': "Missing Identifier"}
        actor_identifier.name = identifier.strip()

    if isinstance(source, basestring):
        source = [create_embedded_source(source,
                                         reference=source_reference,
                                         method=source_method,
                                         analyst=analyst)]

    if source:
        for s in source:
            actor_identifier.add_source(s)
    else:
        return {"success" : False, "message" : "Missing source information."}

    actor_identifier.save(username=analyst)
    actor_identifier.reload()

    return {'success': True,
            'id': str(actor_identifier.id),
            'message': "Actor Identifier added successfully!"}

def actor_identifier_types(active=True):
    """
    Get the available Actor Identifier Types.

    :param active: Only get active ones.
    :type active: boolean
    :returns: list
    """

    if active:
        its = ActorThreatIdentifier.objects(active="on").order_by('+name')
    else:
        its = ActorThreatIdentifier.objects(active="off").order_by('+name')
    it_list = [i.name for i in its]
    return {'items': it_list}

def actor_identifier_type_values(type_=None, username=None):
    """
    Get the available Actor Identifier Type values.

    :param active: Only get active ones.
    :type active: boolean
    :returns: list
    """

    result = {}

    if username and type_:
        sources = user_sources(username)
        ids = ActorIdentifier.objects(active="on",
                                      identifier_type=type_,
                                      source__name__in=sources).order_by('+name')
        result['items'] = [(i.name, i.name) for i in ids]
    else:
        result['items'] = []
    return result

def attribute_actor_identifier(id_, identifier_type, identifier=None,
                               confidence="low", user=None, **kwargs):
    """
    Attribute an Actor Identifier to an Actor in CRITs.

    :param id_: The Actor ObjectId.
    :type id_: str
    :param identifier_type: The Actor Identifier Type.
    :type identifier_type: str
    :param identifier: The Actor Identifier.
    :type identifier: str
    :param user: The user attributing this identifier.
    :type user: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
    """

    sources = user_sources(user)
    admin = is_admin(user)
    actor = Actor.objects(id=id_,
                          source__name__in=sources).first()
    if not actor:
        return {'success': False,
                'message': "Could not find actor"}

    c = len(actor.identifiers)
    actor.attribute_identifier(identifier_type, identifier, confidence, user)
    actor.save(username=user)
    actor.reload()
    actor_identifiers = actor.generate_identifiers_list(user)

    if len(actor.identifiers) <= c:
        return {'success': False,
                'message': "Invalid data submitted or identifier is already attributed."}

    html = render_to_string('actor_identifiers_widget.html',
                            {'actor_identifiers': actor_identifiers,
                             'admin': admin,
                             'actor_id': str(actor.id)})

    return {'success': True,
            'message': html}

def set_identifier_confidence(id_, identifier=None, confidence="low",
                              user=None, **kwargs):
    """
    Set the Identifier attribution confidence.

    :param id_: The ObjectId of the Actor.
    :param identifier: The Actor Identifier ObjectId.
    :type identifier: str
    :param confidence: The confidence level.
    :type confidence: str
    :param user: The user editing this identifier.
    :type user: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
    """

    sources = user_sources(user)
    actor = Actor.objects(id=id_,
                          source__name__in=sources).first()
    if not actor:
        return {'success': False,
                'message': "Could not find actor"}

    actor.set_identifier_confidence(identifier, confidence)
    actor.save(username=user)

    return {'success': True}

def remove_attribution(id_, identifier=None, user=None, **kwargs):
    """
    Remove an attributed identifier.

    :param id_: The ObjectId of the Actor.
    :param identifier: The Actor Identifier ObjectId.
    :type identifier: str
    :param user: The user removing this attribution.
    :type user: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
    """

    sources = user_sources(user)
    admin = is_admin(user)
    actor = Actor.objects(id=id_,
                          source__name__in=sources).first()
    if not actor:
        return {'success': False,
                'message': "Could not find actor"}

    actor.remove_attribution(identifier)
    actor.save(username=user)
    actor.reload()
    actor_identifiers = actor.generate_identifiers_list(user)

    html = render_to_string('actor_identifiers_widget.html',
                            {'actor_identifiers': actor_identifiers,
                             'admin': admin,
                             'actor_id': str(actor.id)})

    return {'success': True,
            'message': html}

def set_actor_name(id_, name, user, **kwargs):
    """
    Set an Actor name.

    :param id_: Actor ObjectId.
    :type id_: str
    :param name: The new name.
    :type name: str
    :param user: The user updating the name.
    :type user: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
    """

    sources = user_sources(user)
    actor = Actor.objects(id=id_,
                          source__name__in=sources).first()
    if not actor:
        return {'success': False,
                'message': "Could not find actor"}

    actor.name = name.strip()
    actor.save(username=user)
    return {'success': True}

def update_actor_aliases(id_, aliases, user, **kwargs):
    """
    Update aliases for an Actor.

    :param id_: The ObjectId of the Actor to update.
    :type id_: str
    :param aliases: The aliases we are setting.
    :type aliases: list
    :param user: The user updating the aliases.
    :type user: str
    :returns: dict
    """

    sources = user_sources(user)
    actor = Actor.objects(id=id_,
                          source__name__in=sources).first()
    if not actor:
        return {'success': False,
                'message': 'No actor could be found.'}
    else:
        actor.update_aliases(aliases)
        actor.save(username=user)
        return {'success': True}
