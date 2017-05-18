import csv
import datetime
import json
import logging
import urlparse

from io import BytesIO
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.urlresolvers import reverse
from django.core.validators import validate_ipv4_address, validate_ipv46_address
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
try:
    from mongoengine.base import ValidationError
except ImportError:
    from mongoengine.errors import ValidationError

from crits.campaigns.forms import CampaignForm
from crits.campaigns.campaign import Campaign
from crits.config.config import CRITsConfig
from crits.core import form_consts
from crits.core.class_mapper import class_from_id
from crits.core.crits_mongoengine import EmbeddedSource, EmbeddedCampaign
from crits.core.crits_mongoengine import json_handler, Action
from crits.core.forms import SourceForm, DownloadFileForm
from crits.core.handlers import build_jtable, csv_export, action_add
from crits.core.handlers import jtable_ajax_list, jtable_ajax_delete
from crits.core.handlers import datetime_parser
from crits.core.user_tools import is_admin, user_sources
from crits.core.user_tools import is_user_subscribed, is_user_favorite
from crits.domains.domain import Domain
from crits.domains.handlers import upsert_domain, get_valid_root_domain
from crits.events.event import Event
from crits.indicators.forms import IndicatorActivityForm
from crits.indicators.indicator import Indicator
from crits.indicators.indicator import EmbeddedConfidence, EmbeddedImpact
from crits.ips.handlers import ip_add_update, validate_and_normalize_ip
from crits.ips.ip import IP
from crits.notifications.handlers import remove_user_from_notification
from crits.services.handlers import run_triage, get_supported_services
from crits.relationships.handlers import get_relationships

from crits.vocabulary.indicators import (
    IndicatorTypes,
    IndicatorThreatTypes,
    IndicatorAttackTypes
)

from crits.vocabulary.ips import IPTypes
from crits.vocabulary.relationships import RelationshipTypes
from crits.vocabulary.status import Status

logger = logging.getLogger(__name__)

def generate_indicator_csv(request):
    """
    Generate a CSV file of the Indicator information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request, Indicator)
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
        if jtable_ajax_delete(obj_type, request):
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
        'fields': list(mapper['jtopts_fields']),
        'hidden_fields': mapper['hidden_fields'],
        'linked_fields': mapper['linked_fields'],
        'details_link': mapper['details_link'],
        'no_sort': mapper['no_sort']
    }
    config = CRITsConfig.objects().first()
    if not config.splunk_search_url:
        del jtopts['fields'][1]
    jtable = build_jtable(jtopts, request)
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
    if config.splunk_search_url:
        for field in jtable['fields']:
            if field['fieldname'].startswith("'splunk"):
                field['display'] = """ function (data) {
                return '<a href="%s' + data.record.value + '"><img src="/new_images/splunk.png" /></a>';
                }
                """ % config.splunk_search_url
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
    relationships = indicator.get_relationships(username=analyst, 
                                                sorted=True, 
                                                meta=True)

    #comments
    comments = {'comments': indicator.get_comments(),
                'url_key': indicator_id}

    #screenshots
    screenshots = indicator.get_screenshots(analyst)

    # favorites
    favorite = is_user_favorite("%s" % analyst, 'Indicator', indicator.id)

    # services
    service_list = get_supported_services('Indicator')

    # analysis results
    service_results = indicator.get_analysis_results()

    args = {'objects': objects,
            'relationships': relationships,
            'comments': comments,
            'relationship': relationship,
            'subscription': subscription,
            "indicator": indicator,
            "forms": forms,
            "indicator_id": indicator_id,
            'screenshots': screenshots,
            'service_list': service_list,
            'service_results': service_results,
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
    if field.get("type") != None and field.get("value") != None:
        return (field.get("type"), field.get("value").lower().strip())

    # this is an email field
    if field.get("field_type") != None and field.get("field_value") != None:
        return (field.get("field_type"), field.get("field_value").lower().strip())

    # otherwise the logic to extract the type/value pair from this
    # specific field type is not supported
    return (None, None)

def get_verified_field(data, valid_values, field=None, default=None):
    """
    Validate and correct string value(s) in a dictionary key or list,
    or a string by itself.

    :param data: The data to be verified and corrected.
    :type data: dict, list of strings, or str
    :param valid_values: Key with simplified string, value with actual string
    :type valid_values: dict
    :param field: The dictionary key containing the data.
    :type field: str
    :param default: A value to use if an invalid item cannot be corrected
    :type default: str
    :returns: the validated/corrected value(str), list of values(list) or ''
    """

    if isinstance(data, dict):
        data = data.get(field, '')
    if isinstance(data, list):
        value_list = data
    else:
        value_list = [data]
    for i, item in enumerate(value_list):
        if isinstance(item, basestring):
            item = item.lower().strip().replace(' - ', '-')
            if item in valid_values:
                value_list[i] = valid_values[item]
                continue
        if default is not None:
            item = default
            continue
        return ''
    if isinstance(data, list):
        return value_list
    else:
        return value_list[0]

def handle_indicator_csv(csv_data, source, method, reference, ctype, username,
                         add_domain=False, related_id=None, related_type=None, relationship_type=None):
    """
    Handle adding Indicators in CSV format (file or blob).

    :param csv_data: The CSV data.
    :type csv_data: str or file handle
    :param source: The name of the source for these indicators.
    :type source: str
    :param method: The method of acquisition of this indicator.
    :type method: str
    :param reference: The reference to this data.
    :type reference: str
    :param ctype: The CSV type.
    :type ctype: str ("file" or "blob")
    :param username: The user adding these indicators.
    :type username: str
    :param add_domain: If the indicators being added are also other top-level
                       objects, add those too.
    :type add_domain: boolean
    :param related_id: ID for object to create relationship with
    :type related_id: str
    :param related_type: Type of object to create relationship with
    :type related_type: str
    :param relationship_type: Type of relationship to create
    :type relationship_type: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    if ctype == "file":
        cdata = csv_data.read()
    else:
        cdata = csv_data.encode('ascii')
    data = csv.DictReader(BytesIO(cdata), skipinitialspace=True)
    result = {'success': True}
    result_message = ""
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
        valid_campaigns[c['name'].lower().replace(' - ', '-')] = c['name']
    valid_actions = {}
    for a in Action.objects(active='on'):
        valid_actions[a['name'].lower().replace(' - ', '-')] = a['name']
    valid_ind_types = {}
    for obj in IndicatorTypes.values(sort=True):
        valid_ind_types[obj.lower().replace(' - ', '-')] = obj

    # Start line-by-line import
    msg = "Cannot process row %s: %s<br />"
    added = 0
    for processed, d in enumerate(data, 1):
        ind = {}
        ind['value'] = (d.get('Indicator') or '').strip()
        ind['lower'] = (d.get('Indicator') or '').lower().strip()
        ind['description'] = (d.get('Description') or '').strip()
        ind['type'] = get_verified_field(d, valid_ind_types, 'Type')
        ind['threat_types'] = d.get('Threat Type',
                                    IndicatorThreatTypes.UNKNOWN).split(',')
        ind['attack_types'] = d.get('Attack Type',
                                    IndicatorAttackTypes.UNKNOWN).split(',')

        if not ind['threat_types'] or ind['threat_types'][0] == '':
            ind['threat_types'] = [IndicatorThreatTypes.UNKNOWN]
        for t in ind['threat_types']:
            if t not in IndicatorThreatTypes.values():
                result['success'] = False
                result_message += msg % (processed + 1, "Invalid Threat Type: %s" % t)
                continue

        if not ind['attack_types'] or ind['attack_types'][0] == '':
            ind['attack_types'] = [IndicatorAttackTypes.UNKNOWN]
        for a in ind['attack_types']:
            if a not in IndicatorAttackTypes.values():
                result['success'] = False
                result_message += msg % (processed + 1, "Invalid Attack Type:%s" % a)
                continue

        ind['status'] = d.get('Status', Status.NEW)
        if not ind['value'] or not ind['type']:
            # Mandatory value missing or malformed, cannot process csv row
            i = ""
            result['success'] = False
            if not ind['value']:
                i += "No valid Indicator value "
            if not ind['type']:
                i += "No valid Indicator type "
            result_message += msg % (processed + 1, i)
            continue
        campaign = get_verified_field(d, valid_campaigns, 'Campaign')
        if campaign:
            ind['campaign'] = campaign
            ind['campaign_confidence'] = get_verified_field(d, valid_campaign_confidence,
                                                            'Campaign Confidence',
                                                            default='low')
        actions = d.get('Action', '')
        if actions:
            actions = get_verified_field(actions.split(','), valid_actions)
            if not actions:
                result['success'] = False
                result_message += msg % (processed + 1, "Invalid Action")
                continue
        ind['confidence'] = get_verified_field(d, valid_ratings, 'Confidence',
                                               default='unknown')
        ind['impact'] = get_verified_field(d, valid_ratings, 'Impact',
                                           default='unknown')
        ind[form_consts.Common.BUCKET_LIST_VARIABLE_NAME] = d.get(form_consts.Common.BUCKET_LIST, '')
        ind[form_consts.Common.TICKET_VARIABLE_NAME] = d.get(form_consts.Common.TICKET, '')
        try:
            response = handle_indicator_insert(ind, source, reference,
                                               analyst=username, method=method,
                                               add_domain=add_domain, related_id=related_id,
                                               related_type=related_type, relationship_type=relationship_type)
        except Exception, e:
            result['success'] = False
            result_message += msg % (processed + 1, e)
            continue
        if response['success']:
            if actions:
                action = {'active': 'on',
                          'analyst': username,
                          'begin_date': '',
                          'end_date': '',
                          'performed_date': '',
                          'reason': '',
                          'date': datetime.datetime.now()}
                for action_type in actions:
                    action['action_type'] = action_type
                    action_add('Indicator', response.get('objectid'), action,
                               user=username)
        else:
            result['success'] = False
            result_message += msg % (processed + 1, response['message'])
            continue
        added += 1
    if processed < 1:
        result['success'] = False
        result_message = "Could not find any valid CSV rows to parse!"
    result['message'] = "Successfully added %s Indicator(s).<br />%s" % (added, result_message)
    return result

def handle_indicator_ind(value, source, ctype, threat_type, attack_type,
                         analyst, status=None, method='', reference='',
                         add_domain=False, add_relationship=False, campaign=None,
                         campaign_confidence=None, confidence=None,
                         description=None, impact=None,
                         bucket_list=None, ticket=None, cache={},
                         related_id=None, related_type=None, relationship_type=None):
    """
    Handle adding an individual indicator.

    :param value: The indicator value.
    :type value: str
    :param source: The name of the source for this indicator.
    :type source: str
    :param ctype: The indicator type.
    :type ctype: str
    :param threat_type: The indicator threat type.
    :type threat_type: str
    :param attack_type: The indicator attack type.
    :type attack_type: str
    :param analyst: The user adding this indicator.
    :type analyst: str
    :param method: The method of acquisition of this indicator.
    :type method: str
    :param reference: The reference to this data.
    :type reference: str
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
    :param description: The description of this data.
    :type description: str
    :param impact: Indicator impact.
    :type impact: str
    :param bucket_list: The bucket(s) to assign to this indicator.
    :type bucket_list: str
    :param ticket: Ticket to associate with this indicator.
    :type ticket: str
    :param cache: Cached data, typically for performance enhancements
                  during bulk uperations.
    :type cache: dict
    :param related_id: ID for object to create relationship with
    :type cache: str
    :param related_type: Type of object to create relationship with
    :type cache: str
    :param relationship_type: Type of relationship to create
    :type cache: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    result = None

    if not source:
        return {"success" : False, "message" : "Missing source information."}

    if threat_type is None:
        threat_type = IndicatorThreatTypes.UNKNOWN
    if attack_type is None:
        attack_type = IndicatorAttackTypes.UNKNOWN
    if description is None:
        description = ''
    if status is None:
        status = Status.NEW

    if value == None or value.strip() == "":
        result = {'success': False,
                  'message': "Can't create indicator with an empty value field"}
    elif ctype == None or ctype.strip() == "":
        result = {'success': False,
                  'message': "Can't create indicator with an empty type field"}
    else:
        ind = {}
        ind['type'] = ctype.strip()
        ind['threat_types'] = [threat_type.strip()]
        ind['attack_types'] = [attack_type.strip()]
        ind['value'] = value.strip()
        ind['lower'] = value.lower().strip()
        ind['description'] = description.strip()
        ind['status'] = status

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
                                           method, add_domain, add_relationship, cache=cache,
                                        related_id=related_id, related_type=related_type,
                                        relationship_type=relationship_type)
        except Exception, e:
            return {'success': False, 'message': repr(e)}

    return result

def handle_indicator_insert(ind, source, reference='', analyst='', method='',
                            add_domain=False, add_relationship=False, cache={},
                            related_id=None, related_type=None, relationship_type=None):
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
    :param related_id: ID for object to create relationship with
    :type cache: str
    :param related_type: Type of object to create relationship with
    :type cache: str
    :param relationship_type: Type of relationship to create
    :type cache: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str) if failed,
              "objectid" (str) if successful,
              "is_new_indicator" (boolean) if successful.
    """

    if ind['type'] not in IndicatorTypes.values():
        return {'success': False,
                'message': "Not a valid Indicator Type: %s" % ind['type']}
    for t in ind['threat_types']:
        if t not in IndicatorThreatTypes.values():
            return {'success': False,
                    'message': "Not a valid Indicator Threat Type: %s" % t}
    for a in ind['attack_types']:
        if a not in IndicatorAttackTypes.values():
            return {'success': False,
                    'message': "Not a valid Indicator Attack Type: " % a}

    (ind['value'], error) = validate_indicator_value(ind['value'], ind['type'])
    if error:
        return {"success": False, "message": error}

    is_new_indicator = False
    dmain = None
    ip = None
    rank = {
        'unknown': 0,
        'benign': 1,
        'low': 2,
        'medium': 3,
        'high': 4,
    }

    if ind.get('status', None) is None or len(ind.get('status', '')) < 1:
        ind['status'] = Status.NEW

    indicator = Indicator.objects(ind_type=ind['type'],
                                  lower=ind['lower']).first()

    if not indicator:
        indicator = Indicator()
        indicator.ind_type = ind.get('type')
        indicator.threat_types = ind.get('threat_types',
                                         IndicatorThreatTypes.UNKNOWN)
        indicator.attack_types = ind.get('attack_types',
                                         IndicatorAttackTypes.UNKNOWN)
        indicator.value = ind.get('value')
        indicator.lower = ind.get('lower')
        indicator.description = ind.get('description', '')
        indicator.created = datetime.datetime.now()
        indicator.confidence = EmbeddedConfidence(analyst=analyst)
        indicator.impact = EmbeddedImpact(analyst=analyst)
        indicator.status = ind.get('status')
        is_new_indicator = True
    else:
        if ind['status'] != Status.NEW:
            indicator.status = ind['status']
        add_desc = "\nSeen on %s as: %s" % (str(datetime.datetime.now()),
                                          ind['value'])
        if not indicator.description:
            indicator.description = ind.get('description', '') + add_desc
        elif indicator.description != ind['description']:
            indicator.description += "\n" + ind.get('description', '') + add_desc
        else:
            indicator.description += add_desc
        indicator.add_threat_type_list(ind.get('threat_types',
                                               IndicatorThreatTypes.UNKNOWN),
                                       analyst,
                                       append=True)
        indicator.add_attack_type_list(ind.get('attack_types',
                                               IndicatorAttackTypes.UNKNOWN),
                                       analyst,
                                       append=True)

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
        if bucket_list:
            indicator.add_bucket_list(bucket_list, analyst)

    ticket = None
    if form_consts.Common.TICKET_VARIABLE_NAME in ind:
        ticket = ind[form_consts.Common.TICKET_VARIABLE_NAME]
        if ticket:
            indicator.add_ticket(ticket, analyst)

    # generate new source information and add to indicator
    if isinstance(source, basestring) and source:
        indicator.add_source(source=source, method=method,
                             reference=reference, analyst=analyst)
    elif isinstance(source, EmbeddedSource):
        indicator.add_source(source_item=source, method=method,
                             reference=reference)
    elif isinstance(source, list):
        for s in source:
            if isinstance(s, EmbeddedSource):
                indicator.add_source(source_item=s, method=method,
                                     reference=reference)

    if add_domain or add_relationship:
        ind_type = indicator.ind_type
        ind_value = indicator.lower
        url_contains_ip = False
        if ind_type in (IndicatorTypes.DOMAIN,
                        IndicatorTypes.URI):
            if ind_type == IndicatorTypes.URI:
                domain_or_ip = urlparse.urlparse(ind_value).hostname
                try:
                    validate_ipv46_address(domain_or_ip)
                    url_contains_ip = True
                except (DjangoValidationError, TypeError):
                    pass
            else:
                domain_or_ip = ind_value
            if not url_contains_ip and domain_or_ip:
                success = None
                if add_domain:
                    success = upsert_domain(domain_or_ip,
                                            indicator.source,
                                            username='%s' % analyst,
                                            campaign=indicator.campaign,
                                            bucket_list=bucket_list,
                                            cache=cache)
                    if not success['success']:
                        return {'success': False, 'message': success['message']}

                if not success or not 'object' in success:
                    dmain = Domain.objects(domain=domain_or_ip).first()
                else:
                    dmain = success['object']

        if ind_type in IPTypes.values() or url_contains_ip:
            if url_contains_ip:
                ind_value = domain_or_ip
                try:
                    validate_ipv4_address(domain_or_ip)
                    ind_type = IndicatorTypes.IPV4_ADDRESS
                except DjangoValidationError:
                    ind_type = IndicatorTypes.IPV6_ADDRESS
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
                    return {'success': False, 'message': success['message']}

            if not success or not 'object' in success:
                ip = IP.objects(ip=indicator.value).first()
            else:
                ip = success['object']

    indicator.save(username=analyst)

    if dmain:
        dmain.add_relationship(indicator,
                               RelationshipTypes.RELATED_TO,
                               analyst="%s" % analyst,
                               get_rels=False)
        dmain.save(username=analyst)
    if ip:
        ip.add_relationship(indicator,
                            RelationshipTypes.RELATED_TO,
                            analyst="%s" % analyst,
                            get_rels=False)
        ip.save(username=analyst)


    # Code for the "Add Related " Dropdown
    related_obj = None
    if related_id:
        related_obj = class_from_id(related_type, related_id)
        if not related_obj:
            return {'success': False,
                    'message': 'Related Object not found.'}

    indicator.save(username=analyst)

    if related_obj and indicator and relationship_type:
        relationship_type=RelationshipTypes.inverse(relationship=relationship_type)
        indicator.add_relationship(related_obj,
                              relationship_type,
                              analyst=analyst,
                              get_rels=False)
        indicator.save(username=analyst)

    # run indicator triage
    if is_new_indicator:
        indicator.reload()
        run_triage(indicator, analyst)

    return {'success': True, 'objectid': str(indicator.id),
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

    type, value = get_indicator_type_value_pair(field)

    if indicator_relationships != None:
        if type != None and value != None:
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

def modify_threat_types(id_, threat_types, user, **kwargs):
    """
    Set the Indicator threat types.

    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :param threat_types: The new indicator threat types.
    :type threat_types: list,str
    :param user: The user updating the indicator.
    :type user: str
    :returns: dict with key "success" (boolean)
    """

    indicator = Indicator.objects(id=id_).first()
    if isinstance(threat_types, basestring):
        threat_types = threat_types.split(',')
    for t in threat_types:
        if t not in IndicatorThreatTypes.values():
            return {'success': False,
                    'message': "Not a valid Threat Type: %s" % t}
    try:
        indicator.add_threat_type_list(threat_types, user, append=False)
        indicator.save(username=user)
        return {'success': True}
    except ValidationError:
        return {'success': False}

def modify_attack_types(id_, attack_types, user, **kwargs):
    """
    Set the Indicator attack type.

    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :param attack_types: The new indicator attack types.
    :type attack_type: list,str
    :param user: The user updating the indicator.
    :type user: str
    :returns: dict with key "success" (boolean)
    """

    indicator = Indicator.objects(id=id_).first()
    if isinstance(attack_types, basestring):
        attack_types = attack_types.split(',')
    for a in attack_types:
        if a not in IndicatorAttackTypes.values():
            return {'success': False,
                    'message': "Not a valid Attack Type: %s" % a}
    try:
        indicator.add_attack_type_list(attack_types, user, append=False)
        indicator.save(username=user)
        return {'success': True}
    except ValidationError:
        return {'success': False}

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
            return {'success': True}
        else:
            return {'success': False, 'message': ['Cannot find Indicator']}
    else:
        return {'success': False, 'message': ['Must be an admin to delete']}

def activity_add(id_, activity, user, **kwargs):
    """
    Add activity to an Indicator.

    :param id_: The ObjectId of the indicator to update.
    :type id_: str
    :param activity: The activity information.
    :type activity: dict
    :param user: The user adding the activitty.
    :type user: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str) if failed,
              "object" (dict) if successful.
    """

    sources = user_sources(user)
    indicator = Indicator.objects(id=id_,
                                  source__name__in=sources).first()
    if not indicator:
        return {'success': False,
                'message': 'Could not find Indicator'}
    try:

        activity['analyst'] = user
        indicator.add_activity(activity['analyst'],
                               activity['start_date'],
                               activity['end_date'],
                               activity['description'],
                               activity['date'])
        indicator.save(username=user)
        return {'success': True, 'object': activity,
                'id': str(indicator.id)}
    except ValidationError, e:
        return {'success': False, 'message': e,
                'id': str(indicator.id)}

def activity_update(id_, activity, user=None, **kwargs):
    """
    Update activity for an Indicator.

    :param id_: The ObjectId of the indicator to update.
    :type id_: str
    :param activity: The activity information.
    :type activity: dict
    :param user: The user updating the activity.
    :type user: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str) if failed,
              "object" (dict) if successful.
    """

    sources = user_sources(user)
    indicator = Indicator.objects(id=id_,
                                  source__name__in=sources).first()
    if not indicator:
        return {'success': False,
                'message': 'Could not find Indicator'}
    try:
        activity = datetime_parser(activity)
        activity['analyst'] = user
        indicator.edit_activity(activity['analyst'],
                                activity['start_date'],
                                activity['end_date'],
                                activity['description'],
                                activity['date'])
        indicator.save(username=user)
        return {'success': True, 'object': activity}
    except ValidationError, e:
        return {'success': False, 'message': e}

def activity_remove(id_, date, user, **kwargs):
    """
    Remove activity from an Indicator.

    :param id_: The ObjectId of the indicator to update.
    :type id_: str
    :param date: The date of the activity to remove.
    :type date: datetime.datetime
    :param user: The user removing this activity.
    :type user: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    indicator = Indicator.objects(id=id_).first()
    if not indicator:
        return {'success': False,
                'message': 'Could not find Indicator'}
    try:

        date = datetime_parser(date)
        indicator.delete_activity(date)
        indicator.save(username=user)
        return {'success': True}
    except ValidationError, e:
        return {'success': False, 'message': e}

def ci_update(id_, ci_type, value, user, **kwargs):
    """
    Update confidence or impact for an indicator.

    :param id_: The ObjectId of the indicator to update.
    :type id_: str
    :param ci_type: What we are updating.
    :type ci_type: str ("confidence" or "impact")
    :param value: The value to set.
    :type value: str ("unknown", "benign", "low", "medium", "high")
    :param user: The user updating this indicator.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    indicator = Indicator.objects(id=id_).first()
    if not indicator:
        return {'success': False,
                'message': 'Could not find Indicator'}
    if ci_type == "confidence" or ci_type == "impact":
        try:
            if ci_type == "confidence":
                indicator.set_confidence(user, value)
            else:
                indicator.set_impact(user, value)
            indicator.save(username=user)
            return {'success': True}
        except ValidationError, e:
            return {'success': False, "message": e}
    else:
        return {'success': False, 'message': 'Invalid CI type'}

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
        ind_type = IPTypes.IPV4_ADDRESS
        ind_class = Indicator.objects(ind_type=ind_type, value=ip).first()

        # setup IP
        if ip_class:
            ip_class.add_relationship(obj_class,
                                      RelationshipTypes.RELATED_TO,
                                      analyst=analyst)
        else:
            ip_class = IP()
            ip_class.ip = ip
            ip_class.source = obj_class.source
            ip_class.save(username=analyst)
            ip_class.add_relationship(obj_class,
                                      RelationshipTypes.RELATED_TO,
                                      analyst=analyst)

        # setup Indicator
        message = ""
        if ind_class:
            message = ind_class.add_relationship(obj_class,
                                                 RelationshipTypes.RELATED_TO,
                                                 analyst=analyst)
            ind_class.add_relationship(ip_class,
                                       RelationshipTypes.RELATED_TO,
                                       analyst=analyst)
        else:
            ind_class = Indicator()
            ind_class.source = obj_class.source
            ind_class.ind_type = ind_type
            ind_class.value = ip
            ind_class.save(username=analyst)
            message = ind_class.add_relationship(obj_class,
                                                 RelationshipTypes.RELATED_TO,
                                                 analyst=analyst)
            ind_class.add_relationship(ip_class,
                                       RelationshipTypes.RELATED_TO,
                                       analyst=analyst)

        # save
        try:
            obj_class.save(username=analyst)
            ip_class.save(username=analyst)
            ind_class.save(username=analyst)
            if message['success']:
                rels = obj_class.get_relationships(username=analyst, sorted=True, meta=True)
                return {'success': True, 'message': rels, 'value': obj_class.id}
            else:
                return {'success': False, 'message': message['message']}
        except Exception, e:
            return {'success': False, 'message': e}
    else:
        return {'success': False,
                'message': "Could not find %s to add relationships" % type_}

def create_indicator_from_tlo(tlo_type, tlo, analyst, source_name=None,
                              tlo_id=None, ind_type=None, value=None,
                              update_existing=True, add_domain=True):
    """
    Create an indicator from a Top-Level Object (TLO).

    :param tlo_type: The CRITs type of the parent TLO.
    :type tlo_type: str
    :param tlo: A CRITs parent TLO class object
    :type tlo: class - some CRITs TLO
    :param analyst: The user creating this indicator.
    :type analyst: str
    :param source_name: The source name for the new source instance that
    records this indicator being added.
    :type source_name: str
    :param tlo_id: The ObjectId of the parent TLO.
    :type tlo_id: str
    :param ind_type: The indicator type, if TLO is not Domain or IP.
    :type ind_type: str
    :param value: The value of the indicator, if TLO is not Domain or IP.
    :type value: str
    :param update_existing: If Indicator already exists, update it
    :type update_existing: boolean
    :param add_domain: If new indicator contains a domain/ip, add a
                       matching Domain or IP TLO
    :type add_domain: boolean
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
              "value" (str),
              "indicator" :class:`crits.indicators.indicator.Indicator`
    """

    if not tlo:
        tlo = class_from_id(tlo_type, tlo_id)
    if not tlo:
        return {'success': False,
                'message': "Could not find %s" % tlo_type}

    source = tlo.source
    campaign = tlo.campaign
    bucket_list = tlo.bucket_list
    tickets = tlo.tickets

    # If value and ind_type provided, use them instead of defaults
    if tlo_type == "Domain":
        value = value or tlo.domain
        ind_type = ind_type or IndicatorTypes.DOMAIN
    elif tlo_type == "IP":
        value = value or tlo.ip
        ind_type = ind_type or tlo.ip_type
    elif tlo_type == "Indicator":
        value = value or tlo.value
        ind_type = ind_type or tlo.ind_type

    if not value or not ind_type: # if not provided & no default
        return {'success': False,
                'message': "Indicator value & type must be provided"
                           "for TLO of type %s" % tlo_type}

    #check if indicator already exists
    if Indicator.objects(ind_type=ind_type,
                         value=value).first() and not update_existing:
        return {'success': False, 'message': "Indicator already exists"}

    result = handle_indicator_ind(value, source,
                                  ctype=ind_type,
                                  threat_type=IndicatorThreatTypes.UNKNOWN,
                                  attack_type=IndicatorAttackTypes.UNKNOWN,
                                  analyst=analyst,
                                  add_domain=add_domain,
                                  add_relationship=True,
                                  campaign=campaign,
                                  bucket_list=bucket_list,
                                  ticket=tickets)

    if result['success']:
        ind = Indicator.objects(id=result['objectid']).first()

        if ind:
            if source_name:
                # add source to show when indicator was created/updated
                ind.add_source(source=source_name,
                               method= 'Indicator created/updated ' \
                                       'from %s with ID %s' % (tlo_type, tlo.id),
                               date=datetime.datetime.now(),
                               analyst = analyst)

            tlo.add_relationship(ind,
                                 RelationshipTypes.RELATED_TO,
                                 analyst=analyst)
            tlo.save(username=analyst)
            for rel in tlo.get_relationships(sorted=True,meta=False)['Event']:
                # Get event object to pass in.
                rel_item = Event.objects(id=rel['other_obj']['obj_id']).first()
                if rel_item:
                    ind.add_relationship(rel_item,
                                         RelationshipTypes.RELATED_TO,
                                         analyst=analyst)
            ind.save(username=analyst)
            tlo.reload()
            rels = tlo.get_relationships(username=analyst,sorted=True, meta=True)
            return {'success': True, 'message': rels,
                    'value': tlo.id, 'indicator': ind}
        else:
            return {'success': False, 'message': "Failed to create Indicator"}
    else:
        return result

def validate_indicator_value(value, ind_type):
    """
    Check that a given value is valid for a particular Indicator type.

    :param value: The value to be validated
    :type value: str
    :param ind_type: The indicator type to validate against
    :type ind_type: str
    :returns: tuple: (Valid value, Error message)
    """

    value = value.strip()
    domain = ""

    # URL
    if ind_type == IndicatorTypes.URI and "://" in value.split('.')[0]:
        domain_or_ip = urlparse.urlparse(value).hostname
        try:
            validate_ipv46_address(domain_or_ip)
            return (value, "")
        except DjangoValidationError:
            domain = domain_or_ip

    # Email address
    if ind_type in (IndicatorTypes.EMAIL_ADDRESS,
                    IndicatorTypes.EMAIL_FROM,
                    IndicatorTypes.EMAIL_REPLY_TO,
                    IndicatorTypes.EMAIL_SENDER):
        if '@' not in value:
            return ("", "Email address must contain an '@'")
        domain_or_ip = value.split('@')[-1]
        if domain_or_ip[0] == '[' and domain_or_ip[-1] == ']':
            try:
                validate_ipv46_address(domain_or_ip[1:-1])
                return (value, "")
            except DjangoValidationError:
                return ("", "Email address does not contain a valid IP")
        else:
            domain = domain_or_ip

    # IPs
    if ind_type in IPTypes.values():
        (ip_address, error) = validate_and_normalize_ip(value, ind_type)
        if error:
            return ("", error)
        else:
            return (ip_address, "")

    # Domains
    if ind_type == IndicatorTypes.DOMAIN or domain:
        (root, domain, error) = get_valid_root_domain(domain or value)
        if error:
            return ("", error)
        else:
            return (value, "")

    return (value, "")
