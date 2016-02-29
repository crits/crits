import json

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
try:
    from mongoengine.base import ValidationError
except ImportError:
    from mongoengine.errors import ValidationError

from crits.core import form_consts
from crits.core.crits_mongoengine import json_handler, EmbeddedCampaign
from crits.core.handlers import jtable_ajax_list, build_jtable, jtable_ajax_delete
from crits.core.handlers import csv_export
from crits.core.user_tools import is_user_subscribed, user_sources
from crits.core.user_tools import is_user_favorite
from crits.emails.email import Email
from crits.services.handlers import run_triage
from crits.stats.handlers import target_user_stats
from crits.targets.division import Division
from crits.targets.forms import TargetInfoForm
from crits.targets.target import Target


def generate_target_csv(request):
    """
    Generate a CSV file of the Target information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request,Target)
    return response

def upsert_target(data, analyst):
    """
    Add/update target information.

    :param data: The target information.
    :type data: dict
    :param analyst: The user adding the target.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    if 'email_address' not in data:
        return {'success': False,
                'message': "No email address to look up"}

    # check for exact match first
    target = Target.objects(email_address=data['email_address']).first()

    if not target: # if no exact match, look for case-insensitive match
        target = Target.objects(email_address__iexact=data['email_address']).first()
    is_new = False
    if not target:
        is_new = True
        target = Target()
        target.email_address = data['email_address'].strip().lower()

    bucket_list = False
    ticket = False
    if 'department' in data:
        target.department = data['department']
    if 'division' in data:
        target.division = data['division']
    if 'organization_id' in data:
        target.organization_id = data['organization_id']
    if 'firstname' in data:
        target.firstname = data['firstname']
    if 'lastname' in data:
        target.lastname = data['lastname']
    if 'note' in data:
        target.note = data['note']
    if 'title' in data:
        target.title = data['title']
    if 'campaign' in data and 'camp_conf' in data:
        target.add_campaign(EmbeddedCampaign(name=data['campaign'],
                                             confidence=data['camp_conf'],
                                             analyst=analyst))
    if 'bucket_list' in data:
        bucket_list = data.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
    if 'ticket' in data:
        ticket = data.get(form_consts.Common.TICKET_VARIABLE_NAME)

    if bucket_list:
        target.add_bucket_list(bucket_list, analyst)

    if ticket:
        target.add_ticket(ticket, analyst)

    try:
        target.save(username=analyst)
        target.reload()
        if is_new:
            run_triage(target, analyst)
        return {'success': True,
                'message': "Target saved successfully",
                'id': str(target.id)}
    except ValidationError, e:
        return {'success': False,
                'message': "Target save failed: %s" % e}

def remove_target(email_address=None, analyst=None):
    """
    Remove a target.

    :param email_address: The email address of the target to remove.
    :type email_address: str
    :param analyst: The user removing the target.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    if not email_address:
        return {'success': False,
                'message': "No email address to look up"}
    target = Target.objects(email_address=email_address).first()
    if not target:
        return {'success': False,
                'message': "No target matching this email address."}
    target.delete(username=analyst)
    return {'success': True,
            'message': "Target removed successfully"}

def get_target_details(email_address, analyst):
    """
    Generate the data to render the Target details template.

    :param email_address: The email address of the target.
    :type email_address: str
    :param analyst: The user requesting this information.
    :type analyst: str
    :returns: template (str), arguments (dict)
    """

    template = None
    if not email_address:
        template = "error.html"
        args = {'error': "Must provide an email address."}
        return template, args

    # check for exact match first
    target = Target.objects(email_address=email_address).first()

    if not target: # if no exact match, look for case-insensitive match
        target = Target.objects(email_address__iexact=email_address).first()
    if not target:
        target = Target()
        target.email_address = email_address.strip().lower()
        form = TargetInfoForm(initial={'email_address': email_address})
    email_list = target.find_emails(analyst)
    form = TargetInfoForm(initial=target.to_dict())

    if form.fields.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME) != None:
        form.fields.pop(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)

    if form.fields.get(form_consts.Common.TICKET_VARIABLE_NAME) != None:
        form.fields.pop(form_consts.Common.TICKET_VARIABLE_NAME)

    subscription = {
        'type': 'Target',
        'id': target.id,
        'subscribed': is_user_subscribed("%s" % analyst,
                                            'Target',
                                            target.id)
    }

    #objects
    objects = target.sort_objects()

    #relationships
    relationships = target.sort_relationships("%s" % analyst,
                                                meta=True)

    # relationship
    relationship = {
            'type': 'Target',
            'value': target.id
    }

    #comments
    if target.id:
        comments = {'comments': target.get_comments(),
                    'url_key': email_address}
    else:
        comments = {'comments': [],
                    'url_key': email_address}

    #screenshots
    screenshots = target.get_screenshots(analyst)

    # favorites
    favorite = is_user_favorite("%s" % analyst, 'Target', target.id)

    # analysis results
    service_results = target.get_analysis_results()

    args = {'objects': objects,
            'relationships': relationships,
            'relationship': relationship,
            'comments': comments,
            'favorite': favorite,
            'subscription': subscription,
            'screenshots': screenshots,
            'email_list': email_list,
            'target_detail': target,
            'service_results': service_results,
            'form': form}

    return template, args

def get_campaign_targets(campaign, user):
    """
    Get targets related to a specific campaign.

    :param campaign: The campaign to search for.
    :type campaign: str
    :param user: The user requesting this information.
    :type user: str
    :returns: list
    """

    # Searching for campaign targets
    sourcefilt = user_sources(user)

    # Get addresses from the 'to' field of emails attributed to this campaign
    emails = Email.objects(source__name__in=sourcefilt,
                           campaign__name=campaign).only('to')
    addresses = {}
    for email in emails:
        for to in email['to']:
            addresses[to.strip().lower()] = 1 # add the way it should be
            addresses[to] = 1 # also add the way it is in the Email

    # Get addresses of Targets attributed to this campaign
    targets = Target.objects(campaign__name=campaign).only('email_address')
    for target in targets:
        addresses[target.email_address] = 1

    uniq_addrs = addresses.keys()
    return uniq_addrs

def generate_target_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    refresh = request.GET.get("refresh", "no")
    if refresh == "yes":
        target_user_stats()
    obj_type = Target
    type_ = "target"
    mapper = obj_type._meta['jtable_opts']
    if option == "jtlist":
        # Handle campaign listings
        query = {}
        if "campaign" in request.GET:
             campaign = request.GET.get("campaign",None)
             emails = get_campaign_targets(campaign, request.user.username)
             query = {"email_address":{"$in": emails}}
        # Sets display url
        details_url = mapper['details_url']
        details_url_key = mapper['details_url_key']
        fields = mapper['fields']
        response = jtable_ajax_list(obj_type, details_url, details_url_key,
                                    request, includes=fields, query=query)
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
        'title': "Targets",
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
            'tooltip': "'All Targets'",
            'text': "'All'",
            'click': "function () {$('#target_listing').jtable('load', {'refresh': 'yes'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'New Targets'",
            'text': "'New'",
            'click': "function () {$('#target_listing').jtable('load', {'refresh': 'yes', 'status': 'New'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'In Progress Targets'",
            'text': "'In Progress'",
            'click': "function () {$('#target_listing').jtable('load', {'refresh': 'yes', 'status': 'In Progress'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Analyzed Targets'",
            'text': "'Analyzed'",
            'click': "function () {$('#target_listing').jtable('load', {'refresh': 'yes', 'status': 'Analyzed'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Deprecated Targets'",
            'text': "'Deprecated'",
            'click': "function () {$('#target_listing').jtable('load', {'refresh': 'yes', 'status': 'Deprecated'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Refresh target stats'",
            'text': "'Refresh'",
            'click': "function () {$.get('"+reverse('crits.%ss.views.%ss_listing' % (type_,type_))+"', {'refresh': 'yes'}); $('target_listing').jtable('load');}",
        },
        {
            'tooltip': "'Add Target'",
            'text': "'Add Target'",
            'click': "function () {$('#new-target').click()}",
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

def generate_division_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    refresh = request.GET.get("refresh", "no")
    if refresh == "yes":
        target_user_stats()
    if option == "jtlist":
        limit = int(request.GET.get('jtPageSize',25))
        skip = int(request.GET.get('jtStartIndex',0))

        response = {}
        response['Result'] = "OK"
        fields = ["division","email_count","id","schema_version"]
        response['TotalRecordCount'] = Division.objects().count()
        response['Records'] = Division.objects().skip(skip).limit(limit).\
                                order_by("-email_count").only(*fields).to_dict()
        #response['Records'] = [d.to_dict() for d in response['Records']]

        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")

    type_ = "division"
    jtopts = {
        'title': "Divisions",
        'default_sort': "email_count DESC",
        'listurl': reverse('crits.targets.views.%ss_listing' % (type_,),
                           args=('jtlist',)),
        'deleteurl': None,
        'searchurl': None,
        'fields': ["division","email_count","id"],
        'hidden_fields': ["_id"],
        'linked_fields': []
    }
    jtable = build_jtable(jtopts,request)
    jtable['toolbar'] = [
        {
            'tooltip': "'Refresh division stats'",
            'text': "'Refresh'",
            'click': "function () {$.get('"+reverse('crits.targets.views.%ss_listing' % (type_))+"', {'refresh': 'yes'}); $('target_listing').jtable('load');}",
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
