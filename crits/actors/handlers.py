import json

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from crits.actors.actor import Actor, ActorIdentifier, ActorThreatIdentifier
from crits.core.class_mapper import class_from_id
from crits.core.crits_mongoengine import EmbeddedCampaign, json_handler
from crits.core.crits_mongoengine import create_embedded_source
from crits.core.forms import DownloadFileForm
from crits.core.handlers import build_jtable, jtable_ajax_list, jtable_ajax_delete
from crits.core.handlers import csv_export
from crits.core.user_tools import is_user_subscribed, user_sources
from crits.core.user_tools import is_user_favorite
from crits.notifications.handlers import remove_user_from_notification
from crits.services.handlers import run_triage, get_supported_services

from crits.vocabulary.actors import (
    ThreatTypes,
    Motivations,
    Sophistications,
    IntendedEffects
)
from crits.vocabulary.relationships import RelationshipTypes
from crits.vocabulary.acls import ActorACL


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
        'listurl': reverse('crits-actors-views-%ss_listing' %
                           (type_), args=('jtlist',)),
        'deleteurl': reverse('crits-actors-views-%ss_listing' %
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
            url = reverse('crits-actors-views-actors_listing')
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
        return render(request, "jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_,
                                   'button': '%ss_tab' % type_},
                                  )
    else:
        return render(request, "%s_listing.html" % type_,
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_},
                                  )

def generate_actor_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    request.user._setup()
    user = request.user

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
        if user.has_access_to(ActorACL.DELETE):
            if jtable_ajax_delete(obj_type, request):
                response = {"Result": "OK"}
            else:
                respones = {"Result": "ERROR"}
        else:
            response = {"Result": "OK",
                        "message": "User does not have permission to delete"}
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    jtopts = {
        'title': "Actors",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits-%ss-views-%ss_listing' %
                           (type_, type_), args=('jtlist',)),
        'deleteurl': reverse('crits-%ss-views-%ss_listing' %
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
        return render(request, "jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_,
                                   'button': '%ss_tab' % type_},
                                  )
    else:
        return render(request, "%s_listing.html" % type_,
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_},
                                  )

def get_actor_details(id_, user):
    """
    Generate the data to render the Actor details template.

    :param id_: The Actor ObjectId to get details for.
    :type actorip: str
    :param user: The user requesting this information.
    :type user: :class:`crits.core.user.CRITsUser`
    :returns: template (str), arguments (dict)
    """

    username = user.username
    allowed_sources = user_sources(username)
    actor = Actor.objects(id=id_, source__name__in=allowed_sources).first()
    template = None
    args = {}

    if not user.check_source_tlp(actor):
        actor = None

    if not actor:
        template = "error.html"
        error = ('Either no data exists for this Actor or you do not have'
                 ' permission to view it.')
        args = {'error': error}
    else:
        actor.sanitize("%s" % username)

        # remove pending notifications for user
        remove_user_from_notification("%s" % username, actor.id, 'Actor')

        download_form = DownloadFileForm(initial={"obj_type": 'Actor',
                                                  "obj_id": actor.id})

        # generate identifiers
        actor_identifiers = actor.generate_identifiers_list(username)

        # subscription
        subscription = {
            'type': 'Actor',
            'id': actor.id,
            'subscribed': is_user_subscribed("%s" % username, 'Actor', actor.id),
        }

        #objects
        objects = actor.sort_objects()

        #relationships
        relationships = actor.sort_relationships("%s" % username, meta=True)

        # relationship
        relationship = {
            'type': 'Actor',
            'value': actor.id
        }

        #comments
        comments = {'comments': actor.get_comments(),
                    'url_key': actor.id}

        #screenshots
        screenshots = actor.get_screenshots(username)

        # favorites
        favorite = is_user_favorite("%s" % username, 'Actor', actor.id)

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
                'comments': comments,
                'ActorACL': ActorACL}
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
                  source_method='', source_reference='', source_tlp=None,
                  campaign=None, confidence=None, user=None,
                  bucket_list=None, ticket=None, related_id=None,
                  related_type=None, relationship_type=None):
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
    :param source_tlp: The TLP for this Actor.
    :type source_tlp: str
    :param campaign: A campaign to attribute to this actor.
    :type campaign: str
    :param confidence: Confidence level in the campaign attribution.
    :type confidence: str ("low", "medium", "high")
    :param user: The user adding this actor.
    :type user: :class:`crits.core.user.CRITsUser`
    :param bucket_list: Buckets to assign to this actor.
    :type bucket_list: str
    :param ticket: Ticket to assign to this actor.
    :type ticket: str
    :param related_id: ID of object to create relationship with
    :type related_id: str
    :param related_type: Type of object to create relationship with
    :type related_id: str
    :param relationship_type: Type of relationship to create.
    :type relationship_type: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
              "object" (if successful) :class:`crits.actors.actor.Actor`
    """

    username = user.username
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
        if user.check_source_write(source):
            source = [create_embedded_source(source,
                                             reference=source_reference,
                                             method=source_method,
                                             tlp=source_tlp,
                                             analyst=username)]
        else:
            return {"success": False,
                    "message": "User does not have permission to add objects \
                    using source %s." % str(source)}

    if isinstance(campaign, basestring):
        c = EmbeddedCampaign(name=campaign,
                             confidence=confidence,
                             analyst=username)
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
        actor.add_bucket_list(bucket_list, username)

    if ticket:
        actor.add_ticket(ticket, username)

    related_obj = None
    if related_id and related_type:
        related_obj = class_from_id(related_type, related_id)
        if not related_obj:
            retVal['success'] = False
            retVal['message'] = 'Related Object not found.'
            return retVal

    actor.save(username=username)

    if related_obj and actor:
            relationship_type=RelationshipTypes.inverse(relationship=relationship_type)
            actor.add_relationship(related_obj,
                                  relationship_type,
                                  analyst=username,
                                  get_rels=False)
            actor.save(username=username)
            actor.reload()

    # run actor triage
    if is_item_new:
        actor.reload()
        run_triage(actor, user)

    resp_url = reverse('crits-actors-views-actor_detail', args=[actor.id])

    retVal['message'] = ('Success! Click here to view the new Actor: '
                         '<a href="%s">%s</a>' % (resp_url, actor.name))

    retVal['success'] = True
    retVal['object'] = actor
    retVal['id'] = str(actor.id)

    return retVal

def actor_remove(id_, user):
    """
    Remove an Actor from CRITs.

    :param id_: The ObjectId of the Actor to remove.
    :type id_: str
    :param user: The user removing this Actor.
    :type user: :class:`crits.core.user.CRITsUser`
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    actor = Actor.objects(id=id_).first()
    if actor:
        actor.delete(username=user.username)
        return {'success': True}
    else:
        return {'success':False, 'message':'Could not find Actor.'}

def create_actor_identifier_type(identifier_type, user):
    """
    Add a new Actor Identifier Type.

    :param identifier_type: The Identifier Type.
    :type identifier_type: str
    :param user: The CRITs user adding the identifier type.
    :type user: :class:`crits.core.user.CRITsUser`
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
        identifier.save(username=user.username)
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

    if tag_type == 'ActorIntendedEffect':
        return IntendedEffects.values(sort=True)
    elif tag_type == 'ActorMotivation':
        return Motivations.values(sort=True)
    elif tag_type == 'ActorSophistication':
        return Sophistications.values(sort=True)
    elif tag_type == 'ActorThreatType':
        return ThreatTypes.values(sort=True)
    else:
        return []

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
        actor.save(username=user.username)
        return {'success': True}

def add_new_actor_identifier(identifier_type, identifier=None, source=None,
                             source_method='', source_reference='',
                             source_tlp=None, user=None):
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
    :param source_tlp: The TLP for this identifier.
    :type source_tlp: str
    :param user: The user adding this actor.
    :type user: :class:`crits.core.user.CRITsUser`
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
                                         tlp=source_tlp,
                                         analyst=user.username)]

    if source:
        for s in source:
            actor_identifier.add_source(s)
    else:
        return {"success" : False, "message" : "Missing source information."}

    actor_identifier.save(username=user.username)
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

def actor_identifier_type_values(type_=None, user=None):
    """
    Get the available Actor Identifier Type values.

    :param active: Only get active ones.
    :type active: boolean
    :returns: list
    """

    result = {}

    if user and type_:
        sources = user.get_sources_list()
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

    if not user:
        return {'success': False,
                'message': "Could not find actor"}
    sources = user.get_sources_list()
    actor = Actor.objects(id=id_,
                          source__name__in=sources).first()
    if not actor:
        return {'success': False,
                'message': "Could not find actor"}

    c = len(actor.identifiers)
    actor.attribute_identifier(identifier_type,
                               identifier,
                               confidence,
                               user.username)
    actor.save(username=user.username)
    actor.reload()
    actor_identifiers = actor.generate_identifiers_list(user.username)

    if len(actor.identifiers) <= c:
        return {'success': False,
                'message': "Invalid data submitted or identifier is already attributed."}

    html = render_to_string('actor_identifiers_widget.html',
                            {'actor_identifiers': actor_identifiers,
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
    :type user: :class:`crits.core.user.CRITsUser`
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
    """

    if not user:
        return {'success': False,
                'message': "Could not find actor"}
    sources = user.get_sources_list()
    actor = Actor.objects(id=id_,
                          source__name__in=sources).first()
    if not actor:
        return {'success': False,
                'message': "Could not find actor"}

    actor.set_identifier_confidence(identifier, confidence)
    actor.save(username=user.username)

    return {'success': True}

def remove_attribution(id_, identifier=None, user=None, **kwargs):
    """
    Remove an attributed identifier.

    :param id_: The ObjectId of the Actor.
    :param identifier: The Actor Identifier ObjectId.
    :type identifier: str
    :param user: The user removing this attribution.
    :type user: :class:`crits.core.user.CRITsUser`
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
    """

    if not user:
        return {'success': False,
                'message': "Could not find actor"}
    sources = user.get_sources_list()
    actor = Actor.objects(id=id_,
                          source__name__in=sources).first()
    if not actor:
        return {'success': False,
                'message': "Could not find actor"}

    actor.remove_attribution(identifier)
    actor.save(username=user.username)
    actor.reload()
    actor_identifiers = actor.generate_identifiers_list(user.username)

    html = render_to_string('actor_identifiers_widget.html',
                            {'actor_identifiers': actor_identifiers,
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
    :type user: :class:`crits.core.user.CRITsUser`
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
    """

    sources = user.get_sources_list()
    actor = Actor.objects(id=id_,
                          source__name__in=sources).first()
    if not actor:
        return {'success': False,
                'message': "Could not find actor"}

    actor.name = name.strip()
    actor.save(username=user.username)
    return {'success': True}

def update_actor_aliases(id_, aliases, user, **kwargs):
    """
    Update aliases for an Actor.

    :param id_: The ObjectId of the Actor to update.
    :type id_: str
    :param aliases: The aliases we are setting.
    :type aliases: list
    :param user: The user updating the aliases.
    :type user: :class:`crits.core.user.CRITsUser`
    :returns: dict
    """

    sources = user.get_sources_list()
    actor = Actor.objects(id=id_,
                          source__name__in=sources).first()
    if not actor:
        return {'success': False,
                'message': 'No actor could be found.'}
    else:
        actor.update_aliases(aliases)
        actor.save(username=user.username)
        return {'success': True}
