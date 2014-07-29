import json

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

import crits.service_env

from crits.actors.actor import Actor, ActorThreatIdentifier
from crits.core.class_mapper import class_from_type
from crits.core.crits_mongoengine import EmbeddedCampaign, json_handler
from crits.core.crits_mongoengine import create_embedded_source
from crits.core.handlers import build_jtable, jtable_ajax_list, jtable_ajax_delete
from crits.core.handlers import csv_export
from crits.core.user_tools import is_admin, is_user_subscribed, user_sources
from crits.core.user_tools import is_user_favorite
from crits.notifications.handlers import remove_user_from_notification
from crits.services.handlers import run_triage

def generate_actor_csv(request):
    """
    Generate a CSV file of the Actor information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request,Actor)
    return response

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
        if jtable_ajax_delete(obj_type,request):
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
    jtable = build_jtable(jtopts,request)
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
                                   'button' : '%ss_tab' % type_},
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

        # generate identifiers
        actor_identifiers = actor.generate_identifiers_list()

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
                    'url_key':actor.id}

        #screenshots
        screenshots = actor.get_screenshots(analyst)

        # favorites
        favorite = is_user_favorite("%s" % analyst, 'Actor', actor.id)

        # services
        manager = crits.service_env.manager
        service_list = manager.get_supported_services('Actor', True)

        args = {'actor_identifiers': actor_identifiers,
                'objects': objects,
                'relationships': relationships,
                'relationship': relationship,
                'subscription': subscription,
                'favorite': favorite,
                'service_list': service_list,
                'screenshots': screenshots,
                'actor': actor,
                'comments':comments}
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
                  source_method=None, source_reference=None, campaign=None,
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

    resp_url = reverse('crits.actors.views.actor_detail', args=[actor.id])

    actor.save(username=analyst)

    # run actor triage
    if is_item_new:
        actor.reload()
        run_triage(None, actor, analyst)

    retVal['message'] = ('Success! Click here to view the new Actor: '
                            '<a href="%s">%s</a>' % (resp_url, actor.id))

    retVal['success'] = True
    retVal['object'] = actor

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
            return {'success':False, 'message':'Could not find Actor.'}
    else:
        return {'success':False, 'message': 'Must be an admin to remove'}

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

def update_actor_tags(actor_id, tag_type, tags, username):
    """
    Update a subset of tags for an Actor.

    :param actor_id: The ObjectId of the Actor to update.
    :type actor_id: str
    :param tag_type: The type of tag we are updating.
    :type tag_type: str
    :param tags: The tags we are setting.
    :type tags: list
    :returns: dict
    """

    actor = Actor.objects(id=actor_id).first()
    if not actor:
        return {'success': False,
                'message': 'No actor could be found.'}
    else:
        actor.update_tags(tag_type, tags)
        actor.save(username=username)
        return {'success': True}
