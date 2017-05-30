import json
import urllib
import logging

from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.core import form_consts
from crits.core.data_tools import json_handler
from crits.core.handsontable_tools import form_to_dict
from crits.core.user_tools import user_can_view_data
from crits.ips.forms import AddIPForm
from crits.ips.handlers import ip_add_update, ip_remove
from crits.ips.handlers import generate_ip_jtable, get_ip_details
from crits.ips.handlers import generate_ip_csv
from crits.ips.handlers import process_bulk_add_ip

from crits.vocabulary.acls import IPACL


@user_passes_test(user_can_view_data)
def ips_listing(request,option=None):
    """
    Generate the IP listing page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', 'csv', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    user = request.user

    if user.has_access_to(IPACL.READ):
        if option == "csv":
            return generate_ip_csv(request)
        return generate_ip_jtable(request, option)
    else:
        return render_to_response("error.html",
                                  {'error': 'User does not have permission to view IP listing.'},
                                  RequestContext(request))


@user_passes_test(user_can_view_data)
def ip_search(request):
    """
    Search for IPs.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    query = {}
    query[request.GET.get('search_type', '')]=request.GET.get('q', '').strip()
    #return render_to_response('error.html', {'error': query})
    return HttpResponseRedirect(reverse('crits.ips.views.ips_listing')
                                + "?%s" % urllib.urlencode(query))

@user_passes_test(user_can_view_data)
def ip_detail(request, ip):
    """
    Generate the IP details page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param ip: The IP to get details for.
    :type ip: str
    :returns: :class:`django.http.HttpResponse`
    """

    user = request.user
    if user.has_access_to(IPACL.READ):
        template = "ip_detail.html"
        (new_template, args) = get_ip_details(ip,
                                              user)
        if new_template:
            template = new_template
        return render_to_response(template,
                                  args,
                                  RequestContext(request))
    else:
        return render_to_response("error.html",
                                  {'error': 'User does not have permission to view IP details.'},
                                  RequestContext(request))


@user_passes_test(user_can_view_data)
def bulk_add_ip(request):
    """
    Bulk add IPs via a bulk upload form.

    Args:
        request: The Django context which contains information about the
            session and key/value pairs for the bulk add IPs request

    Returns:
        If the request is not a POST and not a Ajax call then:
            Returns a rendered HTML form for a bulk add of IPs
        If the request is a POST and a Ajax call then:
            Returns a response that contains information about the
            status of the bulk uploaded IPs. This may include information
            such as IPs that failed or successfully added. This may
            also contain helpful status messages about each operation.
    """

    formdict = form_to_dict(AddIPForm(request.user, None))

    if request.method == "POST" and request.is_ajax():
        response = process_bulk_add_ip(request, formdict)

        return HttpResponse(json.dumps(response,
                            default=json_handler),
                            content_type="application/json")
    else:
        return render_to_response('bulk_add_default.html', {'formdict': formdict,
                                                            'title': "Bulk Add IPs",
                                                            'table_name': 'ip',
                                                            'local_validate_columns': [form_consts.IP.IP_ADDRESS],
                                                            'is_bulk_add_objects': True}, RequestContext(request))

@user_passes_test(user_can_view_data)
def add_update_ip(request, method):
    """
    Add/update an IP address. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param method: If this is an "add" or an "update".
    :type method: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        request.user._setup()
        data = request.POST
        form = AddIPForm(request.user, None, data)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            ip = cleaned_data['ip']
            source_name = cleaned_data['source_name']
            source_reference = cleaned_data['source_reference']
            source_method = cleaned_data['source_method']
            source_tlp= cleaned_data['source_tlp']
            campaign = cleaned_data['campaign']
            confidence = cleaned_data['confidence']
            ip_type = cleaned_data['ip_type']
            add_indicator = False
            if cleaned_data.get('add_indicator'):
                add_indicator = True
            indicator_reference = cleaned_data.get('indicator_reference')
            bucket_list = cleaned_data.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
            ticket = cleaned_data.get(form_consts.Common.TICKET_VARIABLE_NAME)
            related_id = cleaned_data['related_id']
            related_type = cleaned_data['related_type']
            relationship_type = cleaned_data['relationship_type']

            result = ip_add_update(ip,
                                   ip_type,
                                   source=source_name,
                                   source_method=source_method,
                                   source_reference=source_reference,
                                   source_tlp=source_tlp,
                                   campaign=campaign,
                                   confidence=confidence,
                                   user=request.user,
                                   bucket_list=bucket_list,
                                   ticket=ticket,
                                   is_add_indicator=add_indicator,
                                   indicator_reference=indicator_reference,
                                   related_id=related_id,
                                   related_type=related_type,
                                   relationship_type=relationship_type)
            if 'message' in result:
                if not isinstance(result['message'], list):
                    result['message'] = [result['message']]
            else:
                result['message'] = []
                message = ('<div>Success! Click here to view the new IP: <a '
                           'href="%s">%s</a></div>'
                           % (reverse('crits.ips.views.ip_detail',
                                      args=[ip]),
                              ip))
                result['message'].insert(0, message)
            return HttpResponse(json.dumps(result,
                                           default=json_handler),
                                content_type="application/json")

        return HttpResponse(json.dumps({'success': False,
                                        'form':form.as_table()}),
                            content_type="application/json")
    return render_to_response("error.html",
                              {'error': 'Expected AJAX/POST'},
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def remove_ip(request):
    """
    Remove an IP address. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        result = ip_remove(request.POST['key'],
                            request.user.username)
        return HttpResponse(json.dumps(result),
                            mimetype="application/json")

    return render_to_response('error.html',
                              {'error':'Expected AJAX/POST'},
                              RequestContext(request))
