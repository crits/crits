import datetime
import json
import urllib

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string

from crits.core.crits_mongoengine import json_handler
from crits.core.user_tools import user_can_view_data, is_admin
from crits.core import form_consts
from crits.indicators.forms import UploadIndicatorCSVForm
from crits.indicators.forms import UploadIndicatorForm, UploadIndicatorTextForm
from crits.indicators.forms import IndicatorActivityForm
from crits.indicators.handlers import (
    indicator_remove,
    handle_indicator_csv,
    handle_indicator_ind,
    activity_add,
    activity_update,
    activity_remove,
    ci_update,
    create_indicator_and_ip,
    set_indicator_type,
    set_indicator_threat_type,
    set_indicator_attack_type,
    get_indicator_details,
    generate_indicator_jtable,
    generate_indicator_csv,
    create_indicator_from_tlo
)

from crits.vocabulary.indicators import (
    IndicatorTypes,
    IndicatorAttackTypes,
    IndicatorThreatTypes
)

@user_passes_test(user_can_view_data)
def indicator(request, indicator_id):
    """
    Generate Indicator Details template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param indicator_id: The ObjectId of the indicator to get details for.
    :type indicator_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    analyst = request.user.username
    template = "indicator_detail.html"
    (new_template, args) = get_indicator_details(indicator_id,
                                                 analyst)
    if new_template:
        template = new_template
    return render_to_response(template,
                              args,
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def indicators_listing(request, option=None):
    """
    Generate Indicator Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_indicator_csv(request)
    return generate_indicator_jtable(request, option)

@user_passes_test(user_can_view_data)
def remove_indicator(request, _id):
    """
    Remove an Indicator from CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the indicator to remove.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`,
              :class:`django.http.HttpResponseRedirect`
    """

    result = indicator_remove(_id,
                              '%s' % request.user.username)
    if result['success']:
        return HttpResponseRedirect(reverse('crits.indicators.views.indicators_listing'))
    else:
        return render_to_response('error.html',
                                  {'error': result['message']})

@user_passes_test(user_can_view_data)
def indicator_search(request):
    """
    Search for indicators.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    query = {}
    query[request.GET.get('search_type', '')] = request.GET.get('q', '').strip()
    #return render_to_response('error.html', {'error': query})
    return HttpResponseRedirect(reverse('crits.indicators.views.indicators_listing')
                                + "?%s" % urllib.urlencode(query))

@user_passes_test(user_can_view_data)
def upload_indicator(request):
    """
    Upload new indicators (individual, blob, or CSV file).

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
              :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST":
        username = request.user.username
        failed_msg = ''
        result = None

        if request.POST['svalue'] == "Upload CSV":
            form = UploadIndicatorCSVForm(
                username,
                request.POST,
                request.FILES)
            if form.is_valid():
                result = handle_indicator_csv(request.FILES['filedata'],
                                              request.POST['source'],
                                              request.POST['method'],
                                              request.POST['reference'],
                                              "file",
                                              username, add_domain=True,
                                              related_id=request.POST['related_id'],
                                              related_type=request.POST['related_type'],
                                              relationship_type=request.POST['relationship_type'])
                if result['success']:
                    message = {'message': ('<div>%s <a href="%s">Go to all'
                                           ' indicators</a></div>' %
                                           (result['message'],
                                            reverse('crits.indicators.views.indicators_listing')))}
                else:
                    failed_msg = '<div>%s</div>' % result['message']

        if request.POST['svalue'] == "Upload Text":
            form = UploadIndicatorTextForm(username, request.POST)
            if form.is_valid():
                result = handle_indicator_csv(request.POST['data'],
                                              request.POST['source'],
                                              request.POST['method'],
                                              request.POST['reference'],
                                              "ti",
                                              username,
                                              add_domain=True,
                                              related_id=request.POST['related_id'],
                                              related_type=request.POST['related_type'],
                                              relationship_type=request.POST['relationship_type'])
                if result['success']:
                    message = {'message': ('<div>%s <a href="%s">Go to all'
                                           ' indicators</a></div>' %
                                           (result['message'],
                                            reverse('crits.indicators.views.indicators_listing')))}
                else:
                    failed_msg = '<div>%s</div>' % result['message']

        if request.POST['svalue'] == "Upload Indicator":
            form = UploadIndicatorForm(username,
                                       request.POST)
            if form.is_valid():
                result = handle_indicator_ind(
                    request.POST['value'],
                    request.POST['source'],
                    request.POST['indicator_type'],
                    request.POST['threat_type'],
                    request.POST['attack_type'],
                    username,
                    request.POST['method'],
                    request.POST['reference'],
                    add_domain=True,
                    description=request.POST['description'],
                    campaign=request.POST['campaign'],
                    campaign_confidence=request.POST['campaign_confidence'],
                    confidence=request.POST['confidence'],
                    impact=request.POST['impact'],
                    bucket_list=request.POST[form_consts.Common.BUCKET_LIST_VARIABLE_NAME],
                    ticket=request.POST[form_consts.Common.TICKET_VARIABLE_NAME],
                    related_id=request.POST['related_id'],
                    related_type=request.POST['related_type'],
                    relationship_type=request.POST['relationship_type'])
                if result['success']:
                    indicator_link = ((' - <a href=\"%s\">Go to this '
                                       'indicator</a> or <a href="%s">all '
                                       'indicators</a>.</div>') %
                                      (reverse('crits.indicators.views.indicator',
                                               args=[result['objectid']]),
                                       reverse('crits.indicators.views.indicators_listing')))

                    if result.get('is_new_indicator', False) == False:
                        message = {'message': ('<div>Warning: Updated existing'
                                               ' Indicator!' + indicator_link)}
                    else:
                        message = {'message': ('<div>Indicator added '
                                               'successfully!' + indicator_link)}
                else:
                    failed_msg = result['message'] + ' - '

        if result == None or not result['success']:
            failed_msg += ('<a href="%s"> Go to all indicators</a></div>'
                           % reverse('crits.indicators.views.indicators_listing'))
            message = {'message': failed_msg, 'form': form.as_table()}
        elif result != None:
            message['success'] = result['success']

        if request.is_ajax():
            return HttpResponse(json.dumps(message),
                                content_type="application/json")
        else: #file upload
            return render_to_response('file_upload_response.html',
                                      {'response': json.dumps(message)},
                                      RequestContext(request))

@user_passes_test(user_can_view_data)
def add_update_activity(request, method, indicator_id):
    """
    Add/update an indicator's activity. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param method: Whether we are adding or updating.
    :type method: str ("add", "update")
    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        username = request.user.username
        form = IndicatorActivityForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            add = {
                'start_date': data['start_date'] if data['start_date'] else '',
                'end_date': data['end_date'] if data['end_date'] else '',
                'description': data['description'],
            }
            if method == "add":
                add['date'] = datetime.datetime.now()
                result = activity_add(indicator_id, add, username)
            else:
                date = datetime.datetime.strptime(data['date'],
                                                  settings.PY_DATETIME_FORMAT)
                date = date.replace(microsecond=date.microsecond/1000*1000)
                add['date'] = date
                result = activity_update(indicator_id, add, username)
            if 'object' in result:
                result['html'] = render_to_string('indicators_activity_row_widget.html',
                                                  {'activity': result['object'],
                                                   'admin': is_admin(username),
                                                   'indicator_id': indicator_id})
            return HttpResponse(json.dumps(result, default=json_handler),
                                content_type="application/json")
        else: #invalid form
            return HttpResponse(json.dumps({'success': False,
                                            'form': form.as_table()}),
                                content_type="application/json")
    return HttpResponse({})

@user_passes_test(user_can_view_data)
def remove_activity(request, indicator_id):
    """
    Remove an indicator's activity. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        analyst = request.user.username
        if is_admin(analyst):
            date = datetime.datetime.strptime(request.POST['key'],
                                              settings.PY_DATETIME_FORMAT)
            date = date.replace(microsecond=date.microsecond/1000*1000)
            result = activity_remove(indicator_id, date, analyst)
            return HttpResponse(json.dumps(result),
                                content_type="application/json")
        else:
            error = "You do not have permission to remove this item."
            return render_to_response("error.html",
                                      {'error': error},
                                      RequestContext(request))

@user_passes_test(user_can_view_data)
def update_ci(request, indicator_id, ci_type):
    """
    Update an indicator's confidence/impact. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :param ci_type: Whether we are updating confidence or impact.
    :type ci_type: str ("confidence", "impact")
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        value = request.POST['value']
        analyst = request.user.username
        return HttpResponse(json.dumps(ci_update(indicator_id,
                                                 ci_type,
                                                 value,
                                                 analyst)),
                            content_type="application/json")

@user_passes_test(user_can_view_data)
def indicator_and_ip(request):
    """
    Create an Indicator and IP. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        type_ = None
        id_ = None
        ip = None
        if 'type' in request.POST:
            type_ = request.POST['type']
        if 'oid' in request.POST:
            id_ = request.POST['oid']
        if 'ip' in request.POST:
            ip = request.POST['ip']
        if not type_ or not id_ or not ip:
            result = {'success': False,
                      'message': "Need type, oid, and ip"}
        else:
            result = create_indicator_and_ip(type_,
                                             id_,
                                             ip,
                                             request.user.username)
            if result['success']:
                relationship = {'type': type_,
                                'value': result['value']}
                message = render_to_string('relationships_listing_widget.html',
                                           {'relationships': result['message'],
                                            'relationship': relationship},
                                           RequestContext(request))
                result = {'success': True, 'message': message}
            else:
                result = {
                    'success': False,
                    'message': "Error adding relationship: %s" % result['message'],
                }
    else:
        result = {
            'success': False,
            'message': "Expected AJAX POST",
        }
    return HttpResponse(json.dumps(result), content_type="application/json")

@user_passes_test(user_can_view_data)
def indicator_from_tlo(request):
    """
    Create an Indicator from an Top-Level Object. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        ind_type = request.POST.get('ind_type', None)
        tlo_type = request.POST.get('obj_type', None)
        tlo_id = request.POST.get('oid', None)
        value = request.POST.get('value', None)
        source = request.POST.get('source', None)
        if not ind_type or not tlo_type or not tlo_id or not value:
            result = {'success': False,
                      'message': "Need indicator type, tlo type,"
                                 "oid, value, and source."}
        else:
            result = create_indicator_from_tlo(tlo_type,
                                               None,
                                               request.user.username,
                                               source,
                                               tlo_id,
                                               ind_type,
                                               value)
            if result['success']:
                relationship = {'type': ind_type,
                                'value': result['value']}
                message = render_to_string('relationships_listing_widget.html',
                                           {'relationships': result['message'],
                                            'relationship': relationship},
                                           RequestContext(request))
                result = {'success': True, 'message': message}
            else:
                result = {
                    'success':  False,
                    'message':  "Error adding relationship: %s" % result['message']
                }
    else:
        result = {
            'success':  False,
            'message':  "Expected AJAX POST"
        }
    return HttpResponse(json.dumps(result), content_type="application/json")

@user_passes_test(user_can_view_data)
def get_indicator_type_dropdown(request):
    """
    Get Indicator type dropdown data. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        if request.is_ajax():
            dd_final = {}
            list_type = request.POST.get('type', None)
            if list_type == 'indicator_type':
                type_list = IndicatorTypes.values(sort=True)
            elif list_type == 'threat_type':
                type_list = IndicatorThreatTypes.values(sort=True)
            elif list_type == 'attack_type':
                type_list = IndicatorAttackTypes.values(sort=True)
            else:
                type_list = []
            for type_ in type_list:
                dd_final[type_] = type_
            result = {'types': dd_final}
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            error = "Expected AJAX"
            return render_to_response("error.html",
                                      {"error" : error },
                                      RequestContext(request))
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def update_indicator_type(request, indicator_id):
    """
    Update an indicator's type. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        if 'type' in request.POST and len(request.POST['type']) > 0:
            result = set_indicator_type(indicator_id,
                                        request.POST['type'],
                                        '%s' % request.user.username)
            if result['success']:
                message = {'success': True}
            else:
                message = {'success': False}
        else:
            message = {'success': False}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error": error},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def update_indicator_threat_type(request, indicator_id):
    """
    Update an indicator's threat type. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        if 'type' in request.POST and len(request.POST['type']) > 0:
            result = set_indicator_threat_type(indicator_id,
                                        request.POST['type'],
                                        '%s' % request.user.username)
            if result['success']:
                message = {'success': True}
            else:
                message = {'success': False}
        else:
            message = {'success': False}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error": error},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def update_indicator_attack_type(request, indicator_id):
    """
    Update an indicator's attack type. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param indicator_id: The ObjectId of the indicator to update.
    :type indicator_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        if 'type' in request.POST and len(request.POST['type']) > 0:
            result = set_indicator_attack_type(indicator_id,
                                        request.POST['type'],
                                        '%s' % request.user.username)
            if result['success']:
                message = {'success': True}
            else:
                message = {'success': False}
        else:
            message = {'success': False}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error": error},
                                  RequestContext(request))
