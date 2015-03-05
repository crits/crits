import json

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import validate_ipv4_address, validate_ipv6_address
from django.core.validators import validate_ipv46_address
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.core import form_consts
from crits.core.crits_mongoengine import EmbeddedCampaign, json_handler
from crits.core.crits_mongoengine import create_embedded_source
from crits.core.handlers import build_jtable, jtable_ajax_list, jtable_ajax_delete
from crits.core.handsontable_tools import convert_handsontable_to_rows, parse_bulk_upload
from crits.core.data_tools import convert_string_to_bool
from crits.core.handlers import csv_export
from crits.core.user_tools import is_admin, is_user_subscribed, user_sources
from crits.core.user_tools import is_user_favorite
from crits.ips.forms import AddIPForm
from crits.ips.ip import IP
from crits.notifications.handlers import remove_user_from_notification
from crits.objects.handlers import object_array_to_dict, validate_and_add_new_handler_object
from crits.services.handlers import run_triage, get_supported_services

def generate_ip_csv(request):
    """
    Generate a CSV file of the IP information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request,IP)
    return response

def generate_ip_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = IP
    type_ = "ip"
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
        'title': "IPs",
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
            'tooltip': "'All IPs'",
            'text': "'All'",
            'click': "function () {$('#ip_listing').jtable('load', {'refresh': 'yes'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'New IPs'",
            'text': "'New'",
            'click': "function () {$('#ip_listing').jtable('load', {'refresh': 'yes', 'status': 'New'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'In Progress IPs'",
            'text': "'In Progress'",
            'click': "function () {$('#ip_listing').jtable('load', {'refresh': 'yes', 'status': 'In Progress'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Analyzed IPs'",
            'text': "'Analyzed'",
            'click': "function () {$('#ip_listing').jtable('load', {'refresh': 'yes', 'status': 'Analyzed'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Deprecated IPs'",
            'text': "'Deprecated'",
            'click': "function () {$('#ip_listing').jtable('load', {'refresh': 'yes', 'status': 'Deprecated'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Add IP'",
            'text': "'Add IP'",
            'click': "function () {$('#new-ip').click()}",
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

def get_ip_details(ip, analyst):
    """
    Generate the data to render the IP details template.

    :param ip: The IP to get details for.
    :type ip: str
    :param analyst: The user requesting this information.
    :type analyst: str
    :returns: template (str), arguments (dict)
    """

    allowed_sources = user_sources(analyst)
    ip = IP.objects(ip=ip, source__name__in=allowed_sources).first()
    template = None
    args = {}
    if not ip:
        template = "error.html"
        error = ('Either no data exists for this IP or you do not have'
                 ' permission to view it.')
        args = {'error': error}
    else:
        ip.sanitize("%s" % analyst)

        # remove pending notifications for user
        remove_user_from_notification("%s" % analyst, ip.id, 'IP')

        # subscription
        subscription = {
                'type': 'IP',
                'id': ip.id,
                'subscribed': is_user_subscribed("%s" % analyst, 'IP', ip.id),
        }

        #objects
        objects = ip.sort_objects()

        #relationships
        relationships = ip.sort_relationships("%s" % analyst, meta=True)

        # relationship
        relationship = {
                'type': 'IP',
                'value': ip.id
        }

        #comments
        comments = {'comments': ip.get_comments(),
                    'url_key':ip.ip}

        #screenshots
        screenshots = ip.get_screenshots(analyst)

        # favorites
        favorite = is_user_favorite("%s" % analyst, 'IP', ip.id)

        # services
        service_list = get_supported_services('IP')

        # analysis results
        service_results = ip.get_analysis_results()

        args = {'objects': objects,
                'relationships': relationships,
                'relationship': relationship,
                'subscription': subscription,
                'favorite': favorite,
                'service_list': service_list,
                'service_results': service_results,
                'screenshots': screenshots,
                'ip': ip,
                'comments':comments}
    return template, args

def get_ip(allowed_sources, ip_address):
    """
    Get an IP from the database.

    :param allowed_sources: The sources this IP is allowed to have.
    :type allowed_sources: list
    :param ip_address: The IP address to find.
    :type ip_address: str
    :returns: :class:`crits.ips.ip.IP`
    """

    ip = IP.objects(ip=ip_address, source__name__in=allowed_sources).first()
    return ip

def add_new_ip_via_bulk(data, rowData, request, errors, is_validate_only=False, cache={}):
    """
    Bulk add wrapper for the add_new_ip() function.
    """

    return add_new_ip(data, rowData, request, errors, is_validate_only=is_validate_only, cache=cache)

def add_new_ip(data, rowData, request, errors, is_validate_only=False, cache={}):
    """
    Add a new IP to CRITs.

    :param data: Data for the IP address.
    :type data: dict
    :param rowData: Extra data from rows used by mass object uploader.
    :type rowData: dict
    :param request: The request for adding this IP.
    :type request: :class:`django.http.HttpRequest`
    :param errors: A list of current errors prior to processing this IP.
    :type errors: list
    :param is_validate_only: Whether or not we should validate or add.
    :type is_validate_only: bool
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :returns: tuple with (<result>, <errors>, <retval>)
    """

    result = False
    retVal = {}

    ip = data.get('ip')
    ip_type = data.get('ip_type')
    analyst = data.get('analyst')
    campaign = data.get('campaign')
    confidence = data.get('confidence')
    source = data.get('source')
    source_reference = data.get('source_reference')
    is_add_indicator = data.get('add_indicator')
    bucket_list = data.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
    ticket = data.get(form_consts.Common.TICKET_VARIABLE_NAME)
    indicator_reference = data.get('indicator_reference')

    retVal = ip_add_update(ip, ip_type,
            source=source,
            source_reference=source_reference,
            campaign=campaign,
            confidence=confidence,
            analyst=analyst,
            is_add_indicator=is_add_indicator,
            indicator_reference=indicator_reference,
            bucket_list=bucket_list,
            ticket=ticket,
            is_validate_only=is_validate_only,
            cache=cache)

    # This block tries to add objects to the item
    if retVal['success'] == True or is_validate_only == True:
        result = True

        objectsData = rowData.get(form_consts.Common.OBJECTS_DATA)

        # add new objects if they exist
        if objectsData:
            objectsData = json.loads(objectsData)

            for object_row_counter, objectData in enumerate(objectsData, 1):
                new_ip = retVal.get('object')

                if new_ip != None and is_validate_only == False:
                    objectDict = object_array_to_dict(objectData, "IP", new_ip.id)
                else:
                    if new_ip != None:
                        if new_ip.id:
                            objectDict = object_array_to_dict(objectData, "IP", new_ip.id)
                        else:
                            objectDict = object_array_to_dict(objectData, "IP", "")
                    else:
                        objectDict = object_array_to_dict(objectData, "IP", "")

                (object_result, object_errors, object_retVal) = validate_and_add_new_handler_object(
                        None, objectDict, request, errors, object_row_counter,
                        is_validate_only=is_validate_only, cache=cache)

                if object_retVal.get('success') == False:
                    retVal['success'] = False
                if object_retVal.get('message'):
                    errors.append(object_retVal['message'])
    else:
        errors += "Failed to add IP: " + str(ip)

    return result, errors, retVal

def ip_add_update(ip_address, ip_type, source=None, source_method=None,
                  source_reference=None, campaign=None, confidence='low',
                  analyst=None, is_add_indicator=False, indicator_reference=None,
                  bucket_list=None, ticket=None, is_validate_only=False, cache={}):
    """
    Add/update an IP address.

    :param ip_address: The IP to add/update.
    :type ip_address: str
    :param ip_type: The type of IP this is.
    :type ip_type: str
    :param source: Name of the source which provided this information.
    :type source: str
    :param source_method: Method of acquiring this data.
    :type source_method: str
    :param source_reference: A reference to this data.
    :type source_reference: str
    :param campaign: A campaign to attribute to this IP address.
    :type campaign: str
    :param confidence: Confidence level in the campaign attribution.
    :type confidence: str ("low", "medium", "high")
    :param analyst: The user adding/updating this IP.
    :type analyst: str
    :param is_add_indicator: Also add an Indicator for this IP.
    :type is_add_indicator: bool
    :param indicator_reference: Reference for the indicator.
    :type indicator_reference: str
    :param bucket_list: Buckets to assign to this IP.
    :type bucket_list: str
    :param ticket: Ticket to assign to this IP.
    :type ticket: str
    :param is_validate_only: Only validate, do not add/update.
    :type is_validate_only: bool
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
              "object" (if successful) :class:`crits.ips.ip.IP`
    """

    if not source:
        return {"success" : False, "message" : "Missing source information."}

    if "Address - ipv4" in ip_type:
        try:
            validate_ipv4_address(ip_address)
        except ValidationError:
            return {"success": False, "message": "Invalid IPv4 address."}
    elif "Address - ipv6" in ip_type:
        try:
            validate_ipv6_address(ip_address)
        except ValidationError:
            return {"success": False, "message": "Invalid IPv6 address."}
    elif "cidr" in ip_type:
        try:
            if '/' not in ip_address:
                raise ValidationError("")
            cidr_parts = ip_address.split('/')
            if int(cidr_parts[1]) < 0 or int(cidr_parts[1]) > 128:
                raise ValidationError("")
            if ':' not in cidr_parts[0] and int(cidr_parts[1]) > 32:
                raise ValidationError("")
            validate_ipv46_address(cidr_parts[0])
        except (ValidationError, ValueError):
            return {"success": False, "message": "Invalid CIDR address."}
    else:
        return {"success": False, "message": "Invalid IP type."}

    retVal = {}
    is_item_new = False

    ip_object = None
    cached_results = cache.get(form_consts.IP.CACHED_RESULTS)

    if cached_results != None:
        ip_object = cached_results.get(ip_address)
    else:
        ip_object = IP.objects(ip=ip_address).first()

    if not ip_object:
        ip_object = IP()
        ip_object.ip = ip_address
        ip_object.ip_type = ip_type
        is_item_new = True

        if cached_results != None:
            cached_results[ip_address] = ip_object

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
            ip_object.add_campaign(camp)

    if source:
        for s in source:
            ip_object.add_source(s)
    else:
        return {"success" : False, "message" : "Missing source information."}

    if bucket_list:
        ip_object.add_bucket_list(bucket_list, analyst)

    if ticket:
        ip_object.add_ticket(ticket, analyst)

    resp_url = reverse('crits.ips.views.ip_detail', args=[ip_object.ip])

    if is_validate_only == False:
        ip_object.save(username=analyst)

        #set the URL for viewing the new data
        if is_item_new == True:
            retVal['message'] = ('Success! Click here to view the new IP: '
                                 '<a href="%s">%s</a>' % (resp_url, ip_object.ip))
        else:
            message = ('Updated existing IP: '
                                 '<a href="%s">%s</a>' % (resp_url, ip_object.ip))
            retVal['message'] = message
            retVal['status'] = form_consts.Status.DUPLICATE
            retVal['warning'] = message
    elif is_validate_only == True:
        if ip_object.id != None and is_item_new == False:
            message = ('Warning: IP already exists: '
                                 '<a href="%s">%s</a>' % (resp_url, ip_object.ip))
            retVal['message'] = message
            retVal['status'] = form_consts.Status.DUPLICATE
            retVal['warning'] = message

    if is_add_indicator:
        from crits.indicators.handlers import handle_indicator_ind
        handle_indicator_ind(ip_address,
                             source,
                             indicator_reference,
                             ip_type,
                             analyst,
                             source_method,
                             add_domain=False,
                             add_relationship=True,
                             bucket_list=bucket_list,
                             ticket=ticket,
                             cache=cache)

    # run ip triage
    if is_item_new and is_validate_only == False:
        ip_object.reload()
        run_triage(ip_object, analyst)

    retVal['success'] = True
    retVal['object'] = ip_object

    return retVal

def ip_remove(ip_id, username):
    """
    Remove an IP from CRITs.

    :param ip_id: The ObjectId of the IP to remove.
    :type ip_id: str
    :param username: The user removing this IP.
    :type username: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    if is_admin(username):
        ip = IP.objects(id=ip_id).first()
        if ip:
            ip.delete(username=username)
            return {'success': True}
        else:
            return {'success':False, 'message':'Could not find IP.'}
    else:
        return {'success':False, 'message': 'Must be an admin to remove'}

def parse_row_to_bound_ip_form(request, rowData, cache):
    """
    Parse a row out of mass object adder into the
    :class:`crits.ips.forms.AddIPForm`.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :param rowData: The data for that row.
    :type rowData: dict
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :returns: :class:`crits.ips.forms.AddIPForm`.
    """

    # TODO Add common method to convert data to string
    ip = rowData.get(form_consts.IP.IP_ADDRESS, "")
    ip_type = rowData.get(form_consts.IP.IP_TYPE, "")
    # analyst = rowData.get(form_consts.IP.ANALYST, "")
    analyst = request.user
    campaign = rowData.get(form_consts.IP.CAMPAIGN, "")
    confidence = rowData.get(form_consts.IP.CAMPAIGN_CONFIDENCE, "")
    source = rowData.get(form_consts.IP.SOURCE, "")
    source_method = rowData.get(form_consts.IP.SOURCE_METHOD, "")
    source_reference = rowData.get(form_consts.IP.SOURCE_REFERENCE, "")
    is_add_indicator = convert_string_to_bool(rowData.get(form_consts.IP.ADD_INDICATOR, "False"))
    indicator_reference = rowData.get(form_consts.IP.INDICATOR_REFERENCE, "")
    bucket_list = rowData.get(form_consts.Common.BUCKET_LIST, "")
    ticket = rowData.get(form_consts.Common.TICKET, "")

    data = {
        'ip': ip,
        'ip_type': ip_type,
        'analyst': analyst,
        'campaign': campaign,
        'confidence': confidence,
        'source': source,
        'source_method': source_method,
        'source_reference': source_reference,
        'add_indicator': is_add_indicator,
        'indicator_reference': indicator_reference,
        'bucket_list': bucket_list,
        'ticket': ticket}

    bound_form = cache.get('ip_form')

    if bound_form == None:
        bound_form = AddIPForm(request.user, None, data)
        cache['ip_form'] = bound_form
    else:
        bound_form.data = data

    bound_form.full_clean()
    return bound_form

def process_bulk_add_ip(request, formdict):
    """
    Performs the bulk add of ips by parsing the request data. Batches
    some data into a cache object for performance by reducing large
    amounts of single database queries.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param formdict: The form representing the bulk uploaded data.
    :type formdict: dict
    :returns: :class:`django.http.HttpResponse`
    """

    ip_names = []
    cached_results = {}

    cleanedRowsData = convert_handsontable_to_rows(request)
    for rowData in cleanedRowsData:
        if rowData != None and rowData.get(form_consts.IP.IP_ADDRESS) != None:
            ip_names.append(rowData.get(form_consts.IP.IP_ADDRESS).lower())

    ip_results = IP.objects(ip__in=ip_names)

    for ip_result in ip_results:
        cached_results[ip_result.ip] = ip_result

    cache = {form_consts.IP.CACHED_RESULTS: cached_results, 'cleaned_rows_data': cleanedRowsData}

    response = parse_bulk_upload(request, parse_row_to_bound_ip_form, add_new_ip_via_bulk, formdict, cache)

    return response
