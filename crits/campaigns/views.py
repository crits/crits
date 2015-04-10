import datetime
import json

from bson import json_util
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test

from crits.campaigns.forms import AddCampaignForm, CampaignForm
from crits.campaigns.handlers import get_campaign_details, get_campaign_stats
from crits.campaigns.handlers import campaign_add as campaign_addh
from crits.campaigns.handlers import add_campaign as add_campaignh
from crits.campaigns.handlers import campaign_edit, campaign_remove
from crits.campaigns.handlers import add_ttp, edit_ttp, remove_ttp
from crits.campaigns.handlers import modify_campaign_aliases
from crits.campaigns.handlers import generate_campaign_jtable, generate_campaign_csv
from crits.campaigns.handlers import get_campaign_names_list
from crits.core.user_tools import user_can_view_data
from crits.stats.handlers import campaign_date_stats


@user_passes_test(user_can_view_data)
def campaign_stats(request):
    """
    Generate Campaign stats template.

    GET Parameters:
        refresh: Whether or not this is a data refresh (Default: no)
        campaign: Limit to a specific Campaign (Default: all)

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    refresh = request.GET.get("refresh", "no")
    campaign = request.GET.get("campaign", "all")
    if refresh == "yes":
        campaign_date_stats()
    if request.is_ajax():
        data_list = get_campaign_stats(campaign)
        return HttpResponse(json.dumps(data_list,
                                       default=json_util.default),
                            mimetype="application/json")
    else:
        return render_to_response("campaign_monthly.html",
                                  {'campaign': campaign},
                                  RequestContext(request))


@user_passes_test(user_can_view_data)
def campaigns_listing(request, option=None):
    """
    Generate Campaign Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_campaign_csv(request)
    return generate_campaign_jtable(request, option)

@user_passes_test(user_can_view_data)
def campaign_names(request, active_only=True):
    """
    Generate Campaign Listing.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param active_only: Whether we return active campaigns only (default)
    :type active_only: str
    :returns: :class:`django.http.HttpResponse`
    """

    campaign_list = get_campaign_names_list(active_only)
    return HttpResponse(json.dumps(campaign_list), mimetype="application/json")

@user_passes_test(user_can_view_data)
def campaign_details(request, campaign_name):
    """
    Generate Campaign Details template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param campaign_name: The Campaign to get details for.
    :type campaign_name: str
    :returns: :class:`django.http.HttpResponse`
    """

    template = "campaign_detail.html"
    (new_template, args) = get_campaign_details(campaign_name,
                                                request.user.username)
    if new_template:
        template = new_template
    return render_to_response(template,
                              args,
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def add_campaign(request):
    """
    Add a new Campaign to CRITs. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        campaign_form = AddCampaignForm(request.POST)
        if campaign_form.is_valid():
            data = campaign_form.cleaned_data
            campaign_name = data['campaign']
            campaign_aliases = data.get('aliases', None)
            campaign_description = data.get('description', None)
            bucket_list = data.get('bucket_list')
            ticket = data.get('ticket')
            result = add_campaignh(campaign_name,
                                   campaign_description,
                                   campaign_aliases,
                                   request.user.username,
                                   bucket_list=bucket_list,
                                   ticket=ticket)
            if result['success']:
                message = {
                    'message': '<div>Campaign <a href="%s">%s</a> added successfully!</div>' % (reverse('crits.campaigns.views.campaign_details', args=[campaign_name]), campaign_name),
                    'success': True}
            else:
                message = {
                    'message': ['Campaign addition failed!']+result['message'],
                    'success': False}
            return HttpResponse(json.dumps(message), mimetype="application/json")
        else:
            return HttpResponse(json.dumps({'form': campaign_form.as_table(), 'success': False, 'message': "Please correct form errors."}), mimetype="application/json")
    return render_to_response("error.html", {"error": 'Expected AJAX POST'}, RequestContext(request))

@user_passes_test(user_can_view_data)
def campaign_add(request, ctype, objectid):
    """
    Attribute a Campaign to a top-level object. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param ctype: CRITs type for the top-level object.
    :type ctype: str
    :param objectid: The ObjectId of the top-level object.
    :type objectid: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        form = CampaignForm(request.POST)
        result = {}
        if form.is_valid():
            data = form.cleaned_data
            campaign = data['name']
            confidence = data['confidence']
            description = data['description']
            related = data['related']
            analyst = request.user.username
            result = campaign_addh(campaign,
                                   confidence,
                                   description,
                                   related,
                                   analyst,
                                   ctype,
                                   objectid,
                                   update=False)
            if result['success']:
                return HttpResponse(json.dumps(result),
                                    mimetype="application/json")
        result['form'] = form.as_table()
        result['success'] = False
        return HttpResponse(json.dumps(result),
                            mimetype="application/json")
    else:
        return HttpResponse(json.dumps({'success': False,
                                        'message': "Expected AJAX request."}),
                            mimetype="application/json")

@user_passes_test(user_can_view_data)
def edit_campaign(request, ctype, objectid):
    """
    Edit an attributed Campaign for a top-level object. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param ctype: CRITs type for the top-level object.
    :type ctype: str
    :param objectid: The ObjectId of the top-level object.
    :type objectid: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        form = CampaignForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            campaign = data['name']
            confidence = data['confidence']
            description = data['description']
            related = data['related']
            analyst = request.user.username
            try:
                date = datetime.datetime.strptime(data['date'],
                                                  settings.PY_DATETIME_FORMAT)
            except ValueError:
                date = datetime.datetime.now()

            result = campaign_edit(ctype,
                                   objectid,
                                   campaign,
                                   confidence,
                                   description,
                                   date,
                                   related,
                                   analyst)
            if result['success']:
                return HttpResponse(json.dumps(result),
                                    mimetype="application/json")
            else:
                result.update({'form': form.as_table()})
                return HttpResponse(json.dumps(result),
                                    mimetype="application/json")
        else:
            return HttpResponse(json.dumps({'success': False,
                                            'form': form.as_table()}),
                                mimetype="application/json")
    else:
        return HttpResponse(json.dumps({'success': False}),
                            mimetype="application/json")

@user_passes_test(user_can_view_data)
def remove_campaign(request, ctype, objectid):
    """
    Remove an attributed Campaign from a top-level object. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param ctype: CRITs type for the top-level object.
    :type ctype: str
    :param objectid: The ObjectId of the top-level object.
    :type objectid: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        data = request.POST
        result = campaign_remove(ctype,
                                 objectid,
                                 campaign=data.get('key'),
                                 analyst=request.user.username)
        return HttpResponse(json.dumps(result), mimetype="application/json")
    else:
        return render_to_response("error.html",
                                  {"error": 'Expected AJAX POST.'},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def campaign_ttp(request, cid):
    """
    Add/edit/remove a TTP from a Campaign. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param cid: The ObjectId of the Campaign.
    :type cid: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        action = request.POST['action']
        analyst = request.user.username
        if action == "add":
            result = add_ttp(cid, request.POST['ttp'], analyst)
        elif action == "edit":
            result = edit_ttp(cid, request.POST['old_ttp'],
                              request.POST['new_ttp'],
                              analyst)
        elif action == "remove":
            result = remove_ttp(cid, request.POST['ttp'],
                                analyst)
        else:
            result = {'success': False, 'message': "Invalid action."}
        if 'campaign' in result:
            campaign = result['campaign']
            html = render_to_string('campaign_ttps_data_widget.html',
                                    {'campaign_detail': campaign},
                                    RequestContext(request))
            del result['campaign']
            result['html'] = html
        return HttpResponse(json.dumps(result), mimetype="application/json")
    else:
        return render_to_response("error.html",
                                  {"error": 'Expected AJAX POST.'},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def campaign_aliases(request):
    """
    Set Campaign aliases. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        tags = request.POST.get('tags', "").split(",")
        name = request.POST.get('name', None)
        return HttpResponse(json.dumps(modify_campaign_aliases(name,
                                                               tags,
                                                               request.user.username)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html", {"error": error}, RequestContext(request))
