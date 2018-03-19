import json

from django.contrib.auth.decorators import user_passes_test
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render

from crits.core import form_consts
from crits.core.user_tools import user_can_view_data
from crits.pcaps.forms import UploadPcapForm
from crits.pcaps.handlers import handle_pcap_file
from crits.pcaps.handlers import delete_pcap, get_pcap_details
from crits.pcaps.handlers import generate_pcap_jtable, generate_pcap_csv

from crits.vocabulary.acls import PCAPACL

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

    user = request.user

    if user.has_access_to(PCAPACL.READ):
        if option == "csv":
            return generate_pcap_csv(request)
        return generate_pcap_jtable(request, option)
    else:
        return render(request, "error.html",
                                  {'error': 'User does not have permission to view PCAP listing.'})


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
    user = request.user

    if user.has_access_to(PCAPACL.READ):
        (new_template, args) = get_pcap_details(md5, user)
        if new_template:
            template = new_template
        return render(request, template,
                                  args)
    else:
        return render(request, "error.html",
                                  {'error': 'User does not have permission to view PCAP Details.'})

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
            source = cleaned_data.get('source_name')
            tlp = cleaned_data.get('source_tlp')
            user = request.user
            description = cleaned_data.get('description', '')
            related = cleaned_data.get('related_id', '')
            related_type = cleaned_data.get('related_type', '')
            relationship_type = cleaned_data.get('relationship_type', '')
            method = cleaned_data.get('source_method', '') or 'Upload'
            reference = cleaned_data.get('source_reference', '')
            bucket_list=cleaned_data.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
            ticket=cleaned_data.get(form_consts.Common.TICKET_VARIABLE_NAME)
            status = handle_pcap_file(filename, data, source, user, description,
                                      related_id=related, related_type=related_type,
                                      relationship=relationship_type,
                                      method=method, reference=reference, tlp=tlp,
                                      bucket_list=bucket_list, ticket=ticket)
            if status['success']:
                return render(request, 'file_upload_response.html',
                                          {'response': json.dumps({
                    'message': 'PCAP uploaded successfully! <a href="%s">View PCAP</a>'
                        % reverse('crits-pcaps-views-pcap_details',
                                  args=[status['md5']]), 'success': True})},
                                          )
            else:
                return render(request, 'file_upload_response.html', {'response': json.dumps({ 'success': False})})
        else:
            return render(request, 'file_upload_response.html', {'response': json.dumps({'success': False})})
    else:
        return render(request, 'error.html', {'error': "Expected POST."})

@user_passes_test(user_can_view_data)
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
        return HttpResponseRedirect(reverse('crits-pcaps-views-pcaps_listing'))
    else:
        return render(request, 'error.html',
                                  {'error': "Could not delete pcap"})
