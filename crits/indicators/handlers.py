import crits.service_env
import csv
import datetime
import json
import logging
import urlparse

from cStringIO import StringIO
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.urlresolvers import reverse
from django.core.validators import validate_ipv46_address
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from mongoengine.base import ValidationError

from crits.campaigns.forms import CampaignForm
from crits.campaigns.campaign import Campaign
from crits.core import form_consts
from crits.core.class_mapper import class_from_id
from crits.core.crits_mongoengine import EmbeddedSource,EmbeddedCampaign
from crits.core.crits_mongoengine import json_handler
from crits.core.forms import SourceForm, DownloadFileForm
from crits.core.handlers import build_jtable, csv_export
from crits.core.handlers import jtable_ajax_list, jtable_ajax_delete
from crits.core.user_tools import is_admin, user_sources
from crits.core.user_tools import is_user_subscribed, is_user_favorite
from crits.domains.domain import Domain
from crits.domains.handlers import get_domain, upsert_domain
from crits.indicators.forms import IndicatorActionsForm
from crits.indicators.forms import IndicatorActivityForm
from crits.indicators.indicator import IndicatorAction
from crits.indicators.indicator import Indicator
from crits.indicators.indicator import EmbeddedConfidence, EmbeddedImpact
from crits.ips.handlers import ip_add_update
from crits.ips.ip import IP
from crits.notifications.handlers import remove_user_from_notification
from crits.objects.object_type import ObjectType
from crits.raw_data.raw_data import RawData
from crits.services.handlers import run_triage

logger = logging.getLogger(__name__)

def generate_indicator_csv(request):
    """
    Generate a CSV file of the Indicator information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request,Indicator)
    return response

def generate_indicator_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = Indicator
    type_ = "indicator"
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
        'title': "Indicators",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits.%ss.views.%ss_listing' % (type_,
                                                            type_),
                           args=('jtlist',)),
        'deleteurl': reverse('crits.%ss.views.%ss_listing' % (type_,
                                                              type_),
                             args=('jtdelete',)),
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
            'tooltip': "'All Indicators'",
            'text': "'All'",
            'click': "function () {$('#indicator_listing').jtable('load', {'refresh': 'yes'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'New Indicators'",
            'text': "'New'",
            'click': "function () {$('#indicator_listing').jtable('load', {'refresh': 'yes', 'status': 'New'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'In Progress Indicators'",
            'text': "'In Progress'",
            'click': "function () {$('#indicator_listing').jtable('load', {'refresh': 'yes', 'status': 'In Progress'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Analyzed Indicators'",
            'text': "'Analyzed'",
            'click': "function () {$('#indicator_listing').jtable('load', {'refresh': 'yes', 'status': 'Analyzed'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Deprecated Indicators'",
            'text': "'Deprecated'",
            'click': "function () {$('#indicator_listing').jtable('load', {'refresh': 'yes', 'status': 'Deprecated'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Add Indicator'",
            'text': "'Add Indicator'",
            'click': "function () {$('#new-indicator').click()}",
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

def get_indicator_details(indicator_id, analyst):
    """
    Generate the data to render the Indicator details template.

    :param indicator_id: The ObjectId of the Indicator to get details for.
    :type indicator_id: str
    :param analyst: The user requesting this information.
    :type analyst: str
    :returns: template (str), arguments (dict)
    """

    template = None
    users_sources = user_sources(analyst)
    indicator = Indicator.objects(id=indicator_id,
                                  source__name__in=users_sources).first()
    if not indicator:
        error = ("Either this indicator does not exist or you do "
                 "not have permission to view it.")
        template = "error.html"
        args = {'error': error}
        return template, args
    forms = {}
    forms['new_action'] = IndicatorActionsForm(initial={'analyst': analyst,
                                                        'active': "off",
                                                        'date': datetime.datetime.now()})
    forms['new_activity'] = IndicatorActivityForm(initial={'analyst': analyst,
                                                           'date': datetime.datetime.now()})
    forms['new_campaign'] = CampaignForm()#'date': datetime.datetime.now(),
    forms['new_source'] = SourceForm(analyst, initial={'date': datetime.datetime.now()})
    forms['download_form'] = DownloadFileForm(initial={"obj_type": 'Indicator',
                                                       "obj_id": indicator_id})

    indicator.sanitize("%s" % analyst)

    # remove pending notifications for user
    remove_user_from_notification("%s" % analyst, indicator_id, 'Indicator')

    # subscription
    subscription = {
            'type': 'Indicator',
            'id': indicator_id,
            'subscribed': is_user_subscribed("%s" % analyst,
                                             'Indicator',
                                             indicator_id),
    }

    # relationship
    relationship = {
            'type': 'Indicator',
            'value': indicator_id,
    }

    #objects
    objects = indicator.sort_objects()

    #relationships
    relationships = indicator.sort_relationships("%s" % analyst, meta=True)

    #comments
    comments = {'comments': indicator.get_comments(),
                'url_key':indicator_id}

    #screenshots
    screenshots = indicator.get_screenshots(analyst)

    # favorites
    favorite = is_user_favorite("%s" % analyst, 'Indicator', indicator.id)

    # services
    manager = crits.service_env.manager
    service_list = manager.get_supported_services('Indicator', True)

    args = {'objects': objects,
            'relationships': relationships,
            'comments':comments,
            'relationship': relationship,
            'subscription': subscription,
            "indicator": indicator,
            "forms": forms,
            "indicator_id": indicator_id,
            'screenshots': screenshots,
            'service_list': service_list,
            'favorite': favorite,
            'rt_url': settings.RT_URL}

    return template, args

def get_indicator_type_value_pair(field):
    """
    Extracts the type/value pair from a generic field. This is generally used on
    fields that can become indicators such as objects or email fields.
    The type/value pairs are used in indicator relationships
    since indicators are uniquely identified via their type/value pair.
    This function can be used in conjunction with:
        crits.indicators.handlers.does_indicator_relationship_exist

    Args:
        field: The input field containing a type/value pair. This field is
            generally from custom dictionaries such as from Django templates.

    Returns:
        Returns true if the input field already has an indicator associated
        with its values. Returns false otherwise.
    """

    # this is an object
    if field.get("name") != None and field.get("type") != None and field.get("value") != None:
        name = field.get("name")
        type = field.get("type")
        value = field.get("value").lower().strip()
        full_type = type

        if type != name:
            full_type = type + " - " + name

        return (full_type, value)

    # this is an email field
    if field.get("field_type") != None and field.get("field_value") != None:
        return (field.get("field_type"), field.get("field_value").lower().strip())

    # otherwise the logic to extract the type/value pair from this
    # specific field type is not supported
    return (None, None)

def get_verified_field(row, field, valid_values, default=None):
    """
    Validate and correct a key's value from a dictionary
    """

    value = row.get(field, '').strip()
    if value.lower() in valid_values:
        return valid_values[value.lower()]
    elif default is not None:
        return default
    else:
        return ''

def handle_indicator_csv(csv_data, source, reference, ctype, username,
                         add_domain=False):
    """
    Handle adding Indicators in CSV format (file or blob).

    :param csv_data: The CSV data.
    :type csv_data: str or file handle
    :param source: The name of the source for these indicators.
    :type source: str
    :param reference: The reference to this data.
    :type reference: str
    :param ctype: The CSV type.
    :type ctype: str ("file" or "blob")
    :param username: The user adding these indicators.
    :type username: str
    :param add_domain: If the indicators being added are also other top-level
                       objects, add those too.
    :type add_domain: boolean
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    if ctype == "file":
        cdata = csv_data.read()
    else:
        cdata = csv_data.encode('ascii')
    data = csv.DictReader(StringIO(cdata), skipinitialspace=True)
    result = {'success': True}
    result_message = "Indicators added successfully!"
    # Compute permitted values in CSV
    valid_ratings = {
        'unknown': 'unknown',
        'benign': 'benign',
        'low': 'low',
        'medium': 'medium',
        'high': 'high'}
    valid_campaign_confidence = {
        'low': 'low',
        'medium': 'medium',
        'high': 'high'}
    valid_campaigns = {}
    for c in Campaign.objects(active='on'):
        valid_campaigns[c['name'].lower()] = c['name']
    valid_ind_types = {}
    for obj in ObjectType.objects(datatype__enum__exists=False, datatype__file__exists=False):
        if obj['object_type'] == obj['name']:
            name = obj['object_type']
        else:
            name = "%s - %s" % (obj['object_type'], obj['name'])
        valid_ind_types[name.lower()] = name

    # Start line-by-line import
    processed = 0
    for d in data:
        processed += 1
        ind = {}
        ind['value'] = d.get('Indicator', '').lower().strip()
        ind['type'] = get_verified_field(d, 'Type', valid_ind_types)
        if not ind['value'] or not ind['type']:
            # Mandatory value missing or malformed, cannot process csv row
            i = ""
            result['success'] = False
            if not ind['value']:
                i += "No valid Indicator value. "
            if not ind['type']:
                i += "No valid Indicator type. "
            result_message += "Cannot process row: %s. %s<br />" % (processed, i)
            continue
        campaign = get_verified_field(d, 'Campaign', valid_campaigns)
        if campaign:
            ind['campaign'] = campaign
            ind['campaign_confidence'] = get_verified_field(d, 'Campaign Confidence',
                                                            valid_campaign_confidence,
                                                            default='low')
        ind['confidence'] = get_verified_field(d, 'Confidence', valid_ratings,
                                               default='unknown')
        ind['impact'] = get_verified_field(d, 'Impact', valid_ratings,
                                           default='unknown')
        ind[form_consts.Common.BUCKET_LIST_VARIABLE_NAME] = d.get(form_consts.Common.BUCKET_LIST, '')
        ind[form_consts.Common.TICKET_VARIABLE_NAME] = d.get(form_consts.Common.TICKET, '')
        try:
            handle_indicator_insert(ind, source, reference, analyst=username,
                                    add_domain=add_domain)
        except Exception, e:
            result['success'] = False
            result['message'] = str(e)
            return result
    if processed < 1:
        result['success'] = False
        result_message = "Could not find any valid CSV rows to parse!"
    result['message'] = result_message
    return result

def handle_indicator_ind(value, source, reference, ctype, analyst,
                         method='', add_domain=False, add_relationship=False,
                         campaign=None, campaign_confidence=None,
                         confidence=None, impact=None, bucket_list=None,
                         ticket=None, cache={}):
    """
    Handle adding an individual indicator.

    :param value: The indicator value.
    :type value: str
    :param source: The name of the source for this indicator.
    :type source: str
    :param reference: The reference to this data.
    :type reference: str
    :param ctype: The indicator type.
    :type ctype: str
    :param analyst: The user adding this indicator.
    :type analyst: str
    :param method: The method of acquisition of this indicator.
    :type method: str
    :param add_domain: If the indicators being added are also other top-level
                       objects, add those too.
    :type add_domain: boolean
    :param add_relationship: If a relationship can be made, create it.
    :type add_relationship: boolean
    :param campaign: Campaign to attribute to this indicator.
    :type campaign: str
    :param campaign_confidence: Confidence of this campaign.
    :type campaign_confidence: str
    :param confidence: Indicator confidence.
    :type confidence: str
    :param impact: Indicator impact.
    :type impact: str
    :param bucket_list: The bucket(s) to assign to this indicator.
    :type bucket_list: str
    :param ticket: Ticket to associate with this indicator.
    :type ticket: str
    :param cache: Cached data, typically for performance enhancements
                  during bulk uperations.
    :type cache: dict
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    result = None

    if value == None or value.strip() == "":
        result = {'success':  False,
                  'message':  "Can't create indicator with an empty value field"}
    elif ctype == None or ctype.strip() == "":
        result = {'success':  False,
                  'message':  "Can't create indicator with an empty type field"}
    else:
        ind = {}
        ind['type'] = ctype.strip()
        ind['value'] = value.lower().strip()

        if campaign:
            ind['campaign'] = campaign
        if campaign_confidence and campaign_confidence in ('low', 'medium', 'high'):
            ind['campaign_confidence'] = campaign_confidence
        if confidence and confidence in ('unknown', 'benign', 'low', 'medium',
                                         'high'):
            ind['confidence'] = confidence
        if impact and impact in ('unknown', 'benign', 'low', 'medium', 'high'):
            ind['impact'] = impact
        if bucket_list:
            ind[form_consts.Common.BUCKET_LIST_VARIABLE_NAME] = bucket_list
        if ticket:
            ind[form_consts.Common.TICKET_VARIABLE_NAME] = ticket

        try:
            return handle_indicator_insert(ind, source, reference, analyst,
                                           method, add_domain, add_relationship, cache=cache)
        except Exception, e:
            return {'success': False, 'message': repr(e)}

    return result

def handle_indicator_insert(ind, source, reference='', analyst='', method='',
                            add_domain=False, add_relationship=False, cache={}):
    """
    Insert an individual indicator into the database.

    NOTE: Setting add_domain to True will always create a relationship as well.
    However, to create a relationship with an object that already exists before
    this function was called, set add_relationship to True. This will assume
    that the domain or IP object to create the relationship with already exists
    and will avoid infinite mutual calls between, for example, add_update_ip
    and this function. add domain/IP objects.

    :param ind: Information about the indicator.
    :type ind: dict
    :param source: The source for this indicator.
    :type source: list, str, :class:`crits.core.crits_mongoengine.EmbeddedSource`
    :param reference: The reference to the data.
    :type reference: str
    :param analyst: The user adding this indicator.
    :type analyst: str
    :param method: Method of acquiring this indicator.
    :type method: str
    :param add_domain: If this indicator is also a top-level object, try to add
                       it.
    :type add_domain: boolean
    :param add_relationship: Attempt to add relationships if applicable.
    :type add_relationship: boolean
    :param cache: Cached data, typically for performance enhancements
                  during bulk uperations.
    :type cache: dict
    :returns: dict with keys:
              "success" (boolean),
              "message" str) if failed,
              "objectid" (str) if successful,
              "is_new_indicator" (boolean) if successful.
    """

    is_new_indicator = False;
    rank = {
             'unknown': 0,
             'benign': 1,
             'low': 2,
             'medium': 3,
             'high': 4
           }

    indicator = Indicator.objects(ind_type=ind['type'],
                                  value=ind['value']).first()
    if not indicator:
        indicator = Indicator()
        indicator.ind_type = ind['type']
        indicator.value = ind['value']
        indicator.created = datetime.datetime.now()
        indicator.confidence = EmbeddedConfidence(analyst=analyst)
        indicator.impact = EmbeddedImpact(analyst=analyst)
        is_new_indicator = True;

    if 'campaign' in ind:
        if isinstance(ind['campaign'], basestring) and len(ind['campaign']) > 0:
            confidence = ind.get('campaign_confidence', 'low')
            ind['campaign'] = EmbeddedCampaign(name=ind['campaign'],
                                               confidence=confidence,
                                               description="",
                                               analyst=analyst,
                                               date=datetime.datetime.now())
        if isinstance(ind['campaign'], EmbeddedCampaign):
            indicator.add_campaign(ind['campaign'])
        elif isinstance(ind['campaign'], list):
            for campaign in ind['campaign']:
                if isinstance(campaign, EmbeddedCampaign):
                    indicator.add_campaign(campaign)

    if 'confidence' in ind and rank.get(ind['confidence'], 0) > rank.get(indicator.confidence.rating, 0):
        indicator.confidence.rating = ind['confidence']
        indicator.confidence.analyst = analyst

    if 'impact' in ind and rank.get(ind['impact'], 0) > rank.get(indicator.impact.rating, 0):
        indicator.impact.rating = ind['impact']
        indicator.impact.analyst = analyst

    bucket_list = None
    if form_consts.Common.BUCKET_LIST_VARIABLE_NAME in ind:
        bucket_list = ind[form_consts.Common.BUCKET_LIST_VARIABLE_NAME]
        indicator.add_bucket_list(bucket_list, analyst)

    ticket = None
    if form_consts.Common.TICKET_VARIABLE_NAME in ind:
        ticket = ind[form_consts.Common.TICKET_VARIABLE_NAME]
        indicator.add_ticket(ticket, analyst)

    if isinstance(source, list):
        for s in source:
            indicator.add_source(source_item=s)
    elif isinstance(source, EmbeddedSource):
        indicator.add_source(source_item=source)
    elif isinstance(source, basestring):
        s = EmbeddedSource()
        s.name = source
        instance = EmbeddedSource.SourceInstance()
        instance.reference = reference
        instance.method = method
        instance.analyst = analyst
        instance.date = datetime.datetime.now()
        s.instances = [instance]
        indicator.add_source(s)

    indicator.save(username=analyst)

    if add_domain or add_relationship:
        ind_type = indicator.ind_type
        ind_value = indicator.value
        url_contains_ip = False
        if ind_type in ("URI - Domain Name", "URI - URL"):
            if ind_type == "URI - URL":
                domain_or_ip = urlparse.urlparse(ind_value).hostname
            elif ind_type == "URI - Domain Name":
                domain_or_ip = ind_value
            #try:
            (sdomain, fqdn) = get_domain(domain_or_ip)
            if sdomain == "no_tld_found_error" and ind_type == "URI - URL":
                try:
                    validate_ipv46_address(domain_or_ip)
                    url_contains_ip = True
                except DjangoValidationError, e:
                    pass
            if not url_contains_ip:
                success = None
                if add_domain:
                    success = upsert_domain(sdomain, fqdn, indicator.source,
                                            '%s' % analyst, None,
                                            bucket_list=bucket_list, cache=cache)
                    if not success['success']:
                        indicator_link = '<a href=\"%s\">View indicator</a>.</div>' \
                                         % (reverse('crits.indicators.views.indicator', args=[indicator.id]));
                        message = "Indicator was added, but an error occurred. " + indicator_link + "<br>"
                        return {'success':False, 'message':message + success['message']}

                if not success or not 'object' in success:
                    dmain = Domain.objects(domain=domain_or_ip).first()
                else:
                    dmain = success['object']
                if dmain:
                    dmain.add_relationship(rel_item=indicator,
                                           rel_type='Related_To',
                                           analyst="%s" % analyst,
                                           get_rels=False)
                    dmain.save(username=analyst)
                    indicator.save(username=analyst)

        if ind_type.startswith("Address - ip") or ind_type == "Address - cidr" or url_contains_ip:
            if url_contains_ip:
                ind_value = domain_or_ip
            success = None
            if add_domain:
                success = ip_add_update(ind_value,
                                        ind_type,
                                        source=indicator.source,
                                        campaign=indicator.campaign,
                                        analyst=analyst,
                                        bucket_list=bucket_list,
                                        ticket=ticket,
                                        indicator_reference=reference,
                                        cache=cache)
                if not success['success']:
                    indicator_link = '<a href=\"%s\">View indicator</a>.</div>' \
                                     % (reverse('crits.indicators.views.indicator', args=[indicator.id]));
                    message = "Indicator was added, but an error occurred. " + indicator_link + "<br>"
                    return {'success':False, 'message':message + success['message']}

            if not success or not 'object' in success:
                ip = IP.objects(ip=indicator.value).first()
            else:
                ip = success['object']
            if ip:
                ip.add_relationship(rel_item=indicator,
                                    rel_type='Related_To',
                                    analyst="%s" % analyst,
                                    get_rels=False)
                ip.save(username=analyst)
                indicator.save(username=analyst)

    # run indicator triage
    if is_new_indicator:
        indicator.reload()
        run_triage(None, indicator, analyst)

    return {'success': True, 'objectid': indicator.id,
            'is_new_indicator': is_new_indicator, 'object': indicator}

def does_indicator_relationship_exist(field, indicator_relationships):
    """
    Checks if the input field's values already have an indicator
    by cross checking against the list of indicator relationships. The input
    field already has an associated indicator created if the input field's
    "type" and "value" pairs exist -- since indicators are uniquely identified
    by their type/value pair.

    Args:
        field: The generic input field containing a type/value pair. This is
            checked against a list of indicators relationships to see if a
            corresponding indicator already exists. This field is generally
            from custom dictionaries such as from Django templates.
        indicator_relationships: The list of indicator relationships
            to cross reference the input field against.

    Returns:
        Returns true if the input field already has an indicator associated
            with its values. Returns false otherwise.
    """

    (type, value) = get_indicator_type_value_pair(field)

    if indicator_relationships != None:
        if(type != None and value != None):
            for indicator_relationship in indicator_relationships:

                if indicator_relationship == None:
                    logger.error('Indicator relationship is not valid: ' +
                                 str(indicator_relationship))
                    continue

                if type == indicator_relationship.get('ind_type') and value == indicator_relationship.get('ind_value'):
                    return True
        else:
            logger.error('Could not extract type/value pair of input field' +
                         'type: ' + str(type) +
                         'value: ' + (value.encode("utf-8") if value else str(value)) +
                         'indicator_relationships: ' + str(indicator_relationships))

    return False

def ci_search(itype, confidence, impact, actions):
    """
    Find indicators based on type, confidence, impact, and/or actions.

    :param itype: The indicator type to search for.
    :type itype: str
    :param confidence: The confidence level(s) to search for.
    :type confidence: str
    :param impact: The impact level(s) to search for.
    :type impact: str
    :param actions: The action(s) to search for.
    :type actions: str
    :returns: :class:`crits.core.crits_mongoengine.CritsQuerySet`
    """

    query = {}
    if confidence:
        item_list = confidence.replace(' ', '').split(',')
        query["confidence.rating"] = {"$in": item_list}
    if impact:
        item_list = impact.replace(' ', '').split(',')
        query["impact.rating"] = {"$in": item_list}
    if actions:
        item_list = actions.split(',')
        query["actions.action_type"] = {"$in": item_list}
    query["type"] = "%s" % itype.strip()
    result_filter = ('type', 'value', 'confidence', 'impact', 'actions')
    results = Indicator.objects(__raw__=query).only(*result_filter)
    return results

def set_indicator_type(indicator_id, itype, username):
    """
    Set the Indicator type.

    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :param itype: The new indicator type.
    :type itype: str
    :param username: The user updating the indicator.
    :type username: str
    :returns: dict with key "success" (boolean)
    """

    # check to ensure we're not duping an existing indicator
    indicator = Indicator.objects(id=indicator_id).first()
    value = indicator.value
    ind_check = Indicator.objects(ind_type=itype, value=value).first()
    if ind_check:
        # we found a dupe
        return {'success': False}
    else:
        try:
            indicator.ind_type = itype
            indicator.save(username=username)
            return {'success': True}
        except ValidationError:
            return {'success': False}

def add_new_indicator_action(action, analyst):
    """
    Add a new indicator action to CRITs.

    :param action: The action to add to CRITs.
    :type action: str
    :param analyst: The user adding this action.
    :returns: True, False
    """

    action = action.strip()
    try:
        idb_action = IndicatorAction.objects(name=action).first()
        if idb_action:
            return False
        idb_action = IndicatorAction()
        idb_action.name = action
        idb_action.save(username=analyst)
        return True
    except ValidationError:
        return False

def indicator_remove(_id, username):
    """
    Remove an Indicator from CRITs.

    :param _id: The ObjectId of the indicator to remove.
    :type _id: str
    :param username: The user removing the indicator.
    :type username: str
    :returns: dict with keys "success" (boolean) and "message" (list) if failed.
    """

    if is_admin(username):
        indicator = Indicator.objects(id=_id).first()
        if indicator:
            indicator.delete(username=username)
            return {'success':True}
        else:
            return {'success':False,'message':['Cannot find Indicator']}
    else:
        return {'success':False,'message':['Must be an admin to delete']}

def action_add(indicator_id, action):
    """
    Add an action to an indicator.

    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :param action: The information about the action.
    :type action: dict
    :returns: dict with keys:
              "success" (boolean),
              "message" (str) if failed,
              "object" (dict) if successful.
    """

    sources = user_sources(action['analyst'])
    indicator = Indicator.objects(id=indicator_id,
                                  source__name__in=sources).first()
    if not indicator:
        return {'success': False,
                'message': 'Could not find Indicator'}
    try:
        indicator.add_action(action['action_type'],
                             action['active'],
                             action['analyst'],
                             action['begin_date'],
                             action['end_date'],
                             action['performed_date'],
                             action['reason'],
                             action['date'])
        indicator.save(username=action['analyst'])
        return {'success': True, 'object': action}
    except ValidationError, e:
        return {'success': False, 'message': e}

def action_update(indicator_id, action):
    """
    Update an action for an indicator.

    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :param action: The information about the action.
    :type action: dict
    :returns: dict with keys:
              "success" (boolean),
              "message" (str) if failed,
              "object" (dict) if successful.
    """

    sources = user_sources(action['analyst'])
    indicator = Indicator.objects(id=indicator_id,
                                  source__name__in=sources).first()
    if not indicator:
        return {'success': False,
                'message': 'Could not find Indicator'}
    try:
        indicator.edit_action(action['action_type'],
                              action['active'],
                              action['analyst'],
                              action['begin_date'],
                              action['end_date'],
                              action['performed_date'],
                              action['reason'],
                              action['date'])
        indicator.save(username=action['analyst'])
        return {'success': True, 'object': action}
    except ValidationError, e:
        return {'success': False, 'message': e}

def action_remove(indicator_id, date, analyst):
    """
    Remove an action from an indicator.

    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :param date: The date of the action to remove.
    :type date: datetime.datetime
    :param analyst: The user removing the action.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    indicator = Indicator.objects(id=indicator_id).first()
    if not indicator:
        return {'success': False,
                'message': 'Could not find Indicator'}
    try:
        indicator.delete_action(date)
        indicator.save(username=analyst)
        return {'success': True}
    except ValidationError, e:
        return {'success': False, 'message': e}

def activity_add(indicator_id, activity):
    """
    Add activity to an Indicator.

    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :param activity: The activity information.
    :type activity: dict
    :returns: dict with keys:
              "success" (boolean),
              "message" (str) if failed,
              "object" (dict) if successful.
    """

    sources = user_sources(activity['analyst'])
    indicator = Indicator.objects(id=indicator_id,
                                  source__name__in=sources).first()
    if not indicator:
        return {'success': False,
                'message': 'Could not find Indicator'}
    try:
        indicator.add_activity(activity['analyst'],
                               activity['start_date'],
                               activity['end_date'],
                               activity['description'],
                               activity['date'])
        indicator.save(username=activity['analyst'])
        return {'success': True, 'object': activity}
    except ValidationError, e:
        return {'success': False, 'message': e}

def activity_update(indicator_id, activity):
    """
    Update activity for an Indicator.

    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :param activity: The activity information.
    :type activity: dict
    :returns: dict with keys:
              "success" (boolean),
              "message" (str) if failed,
              "object" (dict) if successful.
    """

    sources = user_sources(activity['analyst'])
    indicator = Indicator.objects(id=indicator_id,
                                  source__name__in=sources).first()
    if not indicator:
        return {'success': False,
                'message': 'Could not find Indicator'}
    try:
        indicator.edit_activity(activity['analyst'],
                                activity['start_date'],
                                activity['end_date'],
                                activity['description'],
                                activity['date'])
        indicator.save(username=activity['analyst'])
        return {'success': True, 'object': activity}
    except ValidationError, e:
        return {'success': False, 'message': e}

def activity_remove(indicator_id, date, analyst):
    """
    Remove activity from an Indicator.

    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :param date: The date of the activity to remove.
    :type date: datetime.datetime
    :param analyst: The user removing this activity.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    indicator = Indicator.objects(id=indicator_id).first()
    if not indicator:
        return {'success': False,
                'message': 'Could not find Indicator'}
    try:
        indicator.delete_activity(date)
        indicator.save(username=analyst)
        return {'success': True}
    except ValidationError, e:
        return {'success': False, 'message': e}

def ci_update(indicator_id, ci_type, value, analyst):
    """
    Update confidence or impact for an indicator.

    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :param ci_type: What we are updating.
    :type ci_type: str ("confidence" or "impact")
    :param value: The value to set.
    :type value: str ("unknown", "benign", "low", "medium", "high")
    :param analyst: The user updating this indicator.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    indicator = Indicator.objects(id=indicator_id).first()
    if not indicator:
        return {'success': False,
                'message': 'Could not find Indicator'}
    if ci_type == "confidence" or ci_type == "impact":
        try:
            if ci_type == "confidence":
                indicator.set_confidence(analyst, value)
            else:
                indicator.set_impact(analyst, value)
            indicator.save(username=analyst)
            return {'success': True}
        except ValidationError, e:
            return {'success': False, "message": e}
    else:
        return {'success':False, 'message': 'Invalid CI type'}

def add_indicators_for_domain(domain, fqdn, source, analyst,
                              reference=None, ip=None, bucket_list=None,
                              ticket=None, cache={}):
    """
    Add indicators for a domain.

    :param domain: The domain to add as an Indicator.
    :type domain: str
    :param fqdn: The fully qualified domain (if domain is a root domain).
    :type fqdn: str
    :param source: The source for the indicator.
    :type source: str
    :param analyst: The user adding these indicators.
    :type analyst: str
    :param reference: The reference to this data.
    :type reference: str
    :param ip: An IP address to also generate an indicator out of because it is
               associated with this domain.
    :type ip: :class:`crits.ips.ip.IP`
    :param bucket_list: Buckets to associate with this indicator.
    :type bucket_list: str
    :param ticket: Ticket to associate with this indicator.
    :type ticket: str
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :returns: dict with keys "success" (int) and "errors" (list)
    """

    errors = []
    #add fqdn indicator (Well, could be root, but doesn't matter here. We'll check later.)
    fqdn_result = handle_indicator_ind(fqdn,
                                       source,
                                       reference,
                                       'URI - Domain Name',
                                       analyst,
                                       add_relationship=True,
                                       bucket_list=bucket_list,
                                       ticket=ticket,
                                       cache=cache)
    if not fqdn_result['success']:
        errors += fqdn_result['message']
    if ip:
        #add ip ind and associate with fqdn ind--this will assoc. with
        #   whatever original domain value the user supplied, whether
        #   FQDN or root
        ip_ind = handle_indicator_ind(ip.ip,
                                      ip.source,
                                      reference,
                                      'Address - ipv4-addr',
                                      analyst,
                                      add_relationship=True,
                                      bucket_list=bucket_list,
                                      ticket=ticket,
                                      cache=cache)
        if not ip_ind['success']:
            errors += ip_ind['message']

    if domain != fqdn: #fqdn, so add root indicator as well
        root_ind = handle_indicator_ind(domain,
                                        source,
                                        reference,
                                        'URI - Domain Name',
                                        analyst,
                                        add_relationship=True,
                                        bucket_list=bucket_list,
                                        ticket=ticket,
                                        cache=cache)
        if not root_ind['success']:
            errors.append(u"Error: Root domain indicator could not be added")

    return {'success': len(errors)==0, 'errors':errors}

def create_indicator_and_ip(type_, id_, ip, analyst):
    """
    Add indicators for an IP address.

    :param type_: The CRITs top-level object we are getting this IP from.
    :type type_: class which inherits from
                 :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param id_: The ObjectId of the top-level object to search for.
    :type id_: str
    :param ip: The IP address to generate an indicator out of.
    :type ip: str
    :param analyst: The user adding this indicator.
    :type analyst: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
              "value" (str)
    """

    obj_class = class_from_id(type_, id_)
    if obj_class:
        ip_class = IP.objects(ip=ip).first()
        ind_type = "Address - ipv4-addr"
        ind_class = Indicator.objects(ind_type=ind_type, value=ip).first()

        # setup IP
        if ip_class:
            ip_class.add_relationship(rel_item=obj_class,
                                    rel_type="Related_To",
                                    analyst=analyst)
        else:
            ip_class = IP()
            ip_class.ip = ip
            ip_class.source = obj_class.source
            ip_class.save(username=analyst)
            ip_class.add_relationship(rel_item=obj_class,
                                    rel_type="Related_To",
                                    analyst=analyst)

        # setup Indicator
        message = ""
        if ind_class:
            message = ind_class.add_relationship(rel_item=obj_class,
                                                rel_type="Related_To",
                                                analyst=analyst)
            ind_class.add_relationship(rel_item=ip_class,
                                    rel_type="Related_To",
                                    analyst=analyst)
        else:
            ind_class = Indicator()
            ind_class.source = obj_class.source
            ind_class.ind_type = ind_type
            ind_class.value = ip
            ind_class.save(username=analyst)
            message = ind_class.add_relationship(rel_item=obj_class,
                                                rel_type="Related_To",
                                                analyst=analyst)
            ind_class.add_relationship(rel_item=ip_class,
                                    rel_type="Related_To",
                                    analyst=analyst)

        # save
        try:
            obj_class.save(username=analyst)
            ip_class.save(username=analyst)
            ind_class.save(username=analyst)
            if message['success']:
                rels = obj_class.sort_relationships("%s" % analyst, meta=True)
                return {'success': True, 'message': rels, 'value': obj_class.id}
            else:
                return {'success': False, 'message': message['message']}
        except Exception, e:
            return {'success': False, 'message': e}
    else:
        return {'success': False,
                'message': "Could not find %s to add relationships" % type_}

def create_indicator_from_raw(type_, id_, value, analyst):
    """
    Add indicators from raw data.

    :param type_: The indicator type to add.
    :type type_: str
    :param id_: The ObjectId of the RawData object.
    :type id_: str
    :param value: The value of the indicator to add.
    :type value: str
    :param analyst: The user adding this indicator.
    :type analyst: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
              "value" (str)
    """

    raw_data = RawData.objects(id=id_).first()
    if not raw_data:
        return {'success': False,
                'message': 'Could not find raw data'}
    source = raw_data.source
    bucket_list = raw_data.bucket_list
    campaign = None
    campaign_confidence = None
    if len(raw_data.campaign) > 0:
        campaign = raw_data.campaign[0].name
        campaign_confidence = raw_data.campaign[0].confidence
    result = handle_indicator_ind(value, source, reference=None, ctype=type_,
                                  analyst=analyst,
                                  add_domain=True,
                                  add_relationship=True,
                                  campaign=campaign,
                                  campaign_confidence=campaign_confidence,
                                  bucket_list=bucket_list)
    if result['success']:
        ind = Indicator.objects(id=result['objectid']).first()
        if ind:
            raw_data.add_relationship(rel_item=ind,
                                      rel_type="Related_To",
                                      analyst=analyst)
            raw_data.save(username=analyst)
            for rel in raw_data.relationships:
                if rel.rel_type == "Event":
                    ind.add_relationship(rel_id=rel.object_id,
                                        type_=rel.rel_type,
                                        rel_type="Related_To",
                                        analyst=analyst)
            ind.save(username=analyst)
        raw_data.reload()
        rels = raw_data.sort_relationships("%s" % analyst, meta=True)
        return {'success': True, 'message': rels, 'value': id_}
    else:
        return {'success': False, 'message': result['message']}
