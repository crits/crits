import json

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.backdoors.backdoor import Backdoor
from crits.core.crits_mongoengine import EmbeddedCampaign, json_handler
from crits.core.crits_mongoengine import EmbeddedSource
from crits.core.crits_mongoengine import create_embedded_source
from crits.core.handlers import build_jtable, jtable_ajax_list
from crits.core.handlers import jtable_ajax_delete
from crits.core.handlers import csv_export
from crits.core.user_tools import is_admin, is_user_subscribed, user_sources
from crits.core.user_tools import is_user_favorite
from crits.notifications.handlers import remove_user_from_notification
from crits.services.handlers import run_triage, get_supported_services

def generate_backdoor_csv(request):
    """
    Generate a CSV file of the Backdoor information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request, Backdoor)
    return response

def generate_backdoor_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = Backdoor
    type_ = "backdoor"
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
        'title': "Backdoors",
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
            'tooltip': "'Add Backdoor'",
            'text': "'Add Backdoor'",
            'click': "function () {$('#new-backdoor').click()}",
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

def get_backdoor_details(id_, user):
    """
    Generate the data to render the Backdoor details template.

    :param id_: The Backdoor ObjectId to get details for.
    :type id_: str
    :param user: The user requesting this information.
    :type user: str
    :returns: template (str), arguments (dict)
    """

    allowed_sources = user_sources(user)
    backdoor = Backdoor.objects(id=id_, source__name__in=allowed_sources).first()
    template = None
    args = {}
    if not backdoor:
        template = "error.html"
        error = ('Either no data exists for this Backdoor or you do not have'
                 ' permission to view it.')
        args = {'error': error}
    else:
        backdoor.sanitize("%s" % user)

        # remove pending notifications for user
        remove_user_from_notification("%s" % user, backdoor.id, 'Backdoor')

        # subscription
        subscription = {
            'type': 'Backdoor',
            'id': backdoor.id,
            'subscribed': is_user_subscribed("%s" % user,
                                             'Backdoor',
                                             backdoor.id),
        }

        #objects
        objects = backdoor.sort_objects()

        #relationships
        relationships = backdoor.sort_relationships("%s" % user, meta=True)

        # relationship
        relationship = {
            'type': 'Backdoor',
            'value': backdoor.id
        }

        #comments
        comments = {'comments': backdoor.get_comments(),
                    'url_key': backdoor.id}

        #screenshots
        screenshots = backdoor.get_screenshots(user)

        # favorites
        favorite = is_user_favorite("%s" % user, 'Backdoor', backdoor.id)

        # services
        service_list = get_supported_services('Backdoor')

        # analysis results
        service_results = backdoor.get_analysis_results()

        args = {'objects': objects,
                'relationships': relationships,
                'relationship': relationship,
                'subscription': subscription,
                'favorite': favorite,
                'service_list': service_list,
                'service_results': service_results,
                'screenshots': screenshots,
                'backdoor': backdoor,
                'backdoor_id': id_,
                'comments': comments}
    return template, args

def add_new_backdoor(name, version=None, aliases=None, description=None,
                     source=None, source_method=None, source_reference=None,
                     campaign=None, confidence=None, user=None,
                     bucket_list=None, ticket=None):
    """
    Add an Backdoor to CRITs.

    :param name: The name of the backdoor.
    :type name: str
    :param version: Version of the backdoor.
    :type version: str
    :param aliases: Aliases for the backdoor.
    :type aliases: list or str
    :param description: Description of the backdoor.
    :type description: str
    :param source: Name of the source which provided this information.
    :type source: str
    :param source_method: Method of acquiring this data.
    :type source_method: str
    :param source_reference: A reference to this data.
    :type source_reference: str
    :param campaign: A campaign to attribute to this backdoor.
    :type campaign: str
    :param confidence: Confidence level in the campaign attribution.
    :type confidence: str ("low", "medium", "high")
    :param user: The user adding this backdoor.
    :type user: str
    :param bucket_list: Buckets to assign to this backdoor.
    :type bucket_list: str
    :param ticket: Ticket to assign to this backdoor.
    :type ticket: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
              "id" (str),
              "object" (if successful) :class:`crits.backdoors.backdoor.Backdoor`
    """

    retVal = {'success': False, 'message': ''}

    if isinstance(source, basestring):
        source = [create_embedded_source(source,
                                         reference=source_reference,
                                         method=source_method,
                                         analyst=user)]
    elif isinstance(source, EmbeddedSource):
        source = [source]

    if not source:
        retVal['message'] = "Missing source information."
        return retVal

    # When creating a backdoor object we can potentially create multiple
    # objects. If we are given a name but no version we will create an object
    # with just the name (called the "family backdoor"). If given a name and a
    # version we will create the family backdoor and the specific backdoor for
    # that given version.

    # In case we create more than one backdoor object, store the created ones
    # in this list. The list is walked later on and attributes applied to each
    # object.
    objs = []

    # First check if we have the family (name and no version).
    family = Backdoor.objects(name=name, version='').first()

    if not family:
        # Family does not exist, new object. Details are handled later.
        family = Backdoor()
        family.name = name
        family.version = ''

    objs.append(family)

    # Now check if we have the specific instance for this name + version.
    backdoor = None
    if version:
        backdoor = Backdoor.objects(name=name, version=version).first()
        if not backdoor:
            # Backdoor does not exist, new object. Details are handled later.
            backdoor = Backdoor()
            backdoor.name = name
            backdoor.version = version
        objs.append(backdoor)

    # At this point we have a family object and potentially a specific object.
    # Add the common parameters to all objects in the list and save them.
    for backdoor in objs:
        for s in source:
            backdoor.add_source(s)

        # Don't overwrite existing description.
        if description and backdoor.description == '':
            backdoor.description = description.strip()

        if isinstance(campaign, basestring):
            c = EmbeddedCampaign(name=campaign,
                                 confidence=confidence,
                                 analyst=user)
            campaign = [c]

        if campaign:
            for camp in campaign:
                backdoor.add_campaign(camp)

        if aliases:
            if isinstance(aliases, basestring):
                aliases = aliases.split(',')
            for alias in aliases:
                alias = alias.strip()
                if alias not in backdoor.aliases:
                    backdoor.aliases.append(alias)

        if bucket_list:
            backdoor.add_bucket_list(bucket_list, user)

        if ticket:
            backdoor.add_ticket(ticket, user)

        backdoor.save(username=user)

        # run backdoor triage
        backdoor.reload()
        run_triage(backdoor, user)

        # Because family objects are put in the list first we will always
        # return a link to the most specific object created. If there is only
        # one item in the list it will be the family object.
        resp_url = reverse('crits.backdoors.views.backdoor_detail',
                           args=[backdoor.id])
        retVal['message'] = 'Success: <a href="%s">%s</a>' % (resp_url,
                                                              backdoor.name)
        retVal['object'] = backdoor
        retVal['id'] = str(backdoor.id)

    # If we have a family and specific object, attempt to relate the two.
    if len(objs) == 2:
        objs[0].add_relationship(objs[1], 'Related_To')
        objs[0].save()

    retVal['success'] = True
    return retVal

def backdoor_remove(id_, username):
    """
    Remove a Backdoor from CRITs.

    :param id_: The ObjectId of the Backdoor to remove.
    :type id_: str
    :param username: The user removing this Backdoor.
    :type username: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    if is_admin(username):
        backdoor = Backdoor.objects(id=id_).first()
        if backdoor:
            backdoor.delete(username=username)
            return {'success': True}
        else:
            return {'success': False, 'message': 'Could not find Backdoor.'}
    else:
        return {'success': False, 'message': 'Must be an admin to remove'}

def set_backdoor_name(id_, name, user, **kwargs):
    """
    Set a Backdoor name.

    :param id_: Backdoor ObjectId.
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
    backdoor = Backdoor.objects(id=id_, source__name__in=sources).first()
    if not backdoor:
        return {'success': False, 'message': "Could not find backdoor"}

    # Make sure we don't have a backdoor with that name and new version yet.
    existing_backdoor = Backdoor.objects(name=name,
                                         version=backdoor.version,
                                         source__name__in=sources).first()
    if existing_backdoor:
        # Be sure to return the same error message so backdoors can not be
        # enumerated via this method.
        return {'success': False, 'message': "Could not find backdoor"}

    backdoor.name = name.strip()
    backdoor.save(username=user)
    return {'success': True}

def set_backdoor_version(id_, version, user, **kwargs):
    """
    Set a Backdoor name.

    :param id_: Backdoor ObjectId.
    :type id_: str
    :param version: The new version.
    :type version: str
    :param user: The user updating the version.
    :type user: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
    """

    sources = user_sources(user)
    backdoor = Backdoor.objects(id=id_, source__name__in=sources).first()
    if not backdoor:
        return {'success': False, 'message': "Could not find backdoor"}

    # Make sure we don't have a backdoor with that name and new version yet.
    existing_backdoor = Backdoor.objects(name=backdoor.name,
                                         version=version,
                                         source__name__in=sources).first()
    if existing_backdoor:
        # Be sure to return the same error message so backdoors can not be
        # enumerated via this method.
        return {'success': False, 'message': "Could not find backdoor"}

    backdoor.version = version.strip()
    backdoor.save(username=user)
    return {'success': True}

def update_backdoor_aliases(id_, aliases, user, **kwargs):
    """
    Update aliases for a Backdoor.

    :param id_: The ObjectId of the Backdoor to update.
    :type id_: str
    :param aliases: The aliases we are setting.
    :type aliases: list
    :param user: The user updating the aliases.
    :type user: str
    :returns: dict
    """

    sources = user_sources(user)
    backdoor = Backdoor.objects(id=id_, source__name__in=sources).first()
    if not backdoor:
        return {'success': False,
                'message': 'No backdoor could be found.'}
    else:
        backdoor.update_aliases(aliases)
        backdoor.save(username=user)
        return {'success': True}

def get_backdoor_names(user, **kwargs):
    """
    Get a list of unique backdoor names.

    :param user: The user requesting the names.
    :returns: list of tuples
    """

    sources = user_sources(user)
    only = ('name', 'version')
    bds = Backdoor.objects(source__name__in=sources).only(*only)

    names = []
    for b in bds:
        if (b.name, b.version) not in names:
            names.append((b.name, b.version))
    return names

