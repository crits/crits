import json

from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.core import form_consts
from crits.core.user_tools import user_can_view_data
from crits.core.user_tools import user_is_admin
from crits.pcaps.forms import UploadPcapForm
from crits.pcaps.handlers import handle_pcap_file
from crits.pcaps.handlers import delete_pcap, get_pcap_details
from crits.pcaps.handlers import generate_pcap_jtable, generate_pcap_csv

@user_passes_test(user_can_view_data)
def pcaps_listing(request,option=None):
    """
    Generate PCAP Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_pcap_csv(request)
    return generate_pcap_jtable(request, option)

@user_passes_test(user_can_view_data)
def pcap_details(request, md5):
    """
    Generate PCAP Details template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param md5: The MD5 of the PCAP.
    :type md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    template = 'pcap_detail.html'
    analyst = request.user.username
    (new_template, args) = get_pcap_details(md5, analyst)
    if new_template:
        template = new_template
    return render_to_response(template,
                              args,
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def upload_pcap(request):
    """
    Add a new PCAP to CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        form = UploadPcapForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            filedata = request.FILES['filedata']
            filename = filedata.name
            data = filedata.read() # XXX: Should be using chunks here.
            source = cleaned_data.get('source')
            user = request.user.username
            description = cleaned_data.get('description', '')
            related = cleaned_data.get('related_id', '')
            related_type = cleaned_data.get('related_type', '')
            relationship_type = cleaned_data.get('relationship_type', '')
            method = cleaned_data.get('method', '') or 'Upload'
            reference = cleaned_data.get('reference', '')
            bucket_list=cleaned_data.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
            ticket=cleaned_data.get(form_consts.Common.TICKET_VARIABLE_NAME)
            status = handle_pcap_file(filename, data, source, user, description,
                                      related_id=related, related_type=related_type,
                                      relationship=relationship_type,
                                      method=method, reference=reference,
                                      bucket_list=bucket_list, ticket=ticket)
            if status['success']:
                return render_to_response('file_upload_response.html',
                                          {'response': json.dumps({
                    'message': 'PCAP uploaded successfully! <a href="%s">View PCAP</a>'
                        % reverse('crits.pcaps.views.pcap_details',
                                  args=[status['md5']]), 'success': True})},
                                          RequestContext(request))
            else:
                return render_to_response('file_upload_response.html',
                                          {'response': json.dumps({ 'success': False,
                                                                   'message': status['message']})}
                                          , RequestContext(request))
        else:
            return render_to_response('file_upload_response.html',
                                      {'response': json.dumps({'success': False,
                                                               'form': form.as_table()})},
                RequestContext(request))
    else:
        return render_to_response('error.html',
                                  {'error': "Expected POST."},
                                  RequestContext(request))

@user_passes_test(user_is_admin)
def remove_pcap(request, md5):
    """
    Remove a PCAP from CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param md5: The MD5 of the PCAP.
    :type md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    result = delete_pcap(md5, '%s' % request.user.username)
    if result:
        return HttpResponseRedirect(reverse('crits.pcaps.views.pcaps_listing'))
    else:
        return render_to_response('error.html',
                                  {'error': "Could not delete pcap"})
