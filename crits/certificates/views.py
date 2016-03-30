import json

from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.core import form_consts
from crits.core.user_tools import user_can_view_data
from crits.core.user_tools import user_is_admin
from crits.certificates.forms import UploadCertificateForm
from crits.certificates.handlers import handle_cert_file
from crits.certificates.handlers import delete_cert, get_certificate_details
from crits.certificates.handlers import generate_cert_jtable, generate_cert_csv

@user_passes_test(user_can_view_data)
def certificates_listing(request,option=None):
    """
    Generate Certificate Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_cert_csv(request)
    return generate_cert_jtable(request, option)

@user_passes_test(user_can_view_data)
def certificate_details(request, md5):
    """
    Generate Certificate Details template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param md5: The MD5 of the Certificate.
    :type md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    template = 'certificate_details.html'
    analyst = request.user.username
    (new_template, args) = get_certificate_details(md5, analyst)
    if new_template:
        template = new_template
    return render_to_response(template,
                              args,
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def upload_certificate(request):
    """
    Add a new Certificate to CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        form = UploadCertificateForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            filedata = request.FILES['filedata']
            filename = filedata.name
            data = filedata.read() # XXX: Should be using chunks here.
            source = form.cleaned_data.get('source')
            user = request.user.username
            description = form.cleaned_data.get('description', '')
            related = form.cleaned_data.get('related_id', '')
            related_type = form.cleaned_data.get('related_type', '')
            relationship_type = form.cleaned_data.get('relationship_type','')
            bucket_list = form.cleaned_data.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
            ticket = form.cleaned_data.get(form_consts.Common.TICKET_VARIABLE_NAME)
            method = form.cleaned_data.get('method', '') or 'Upload'
            reference = form.cleaned_data.get('reference', '')
            status = handle_cert_file(filename, data, source, user, description,
                                      related_id=related, related_type=related_type,
                                      relationship_type=relationship_type, method=method, 
                                      reference=reference, bucket_list=bucket_list, ticket=ticket)
            if status['success']:
                return render_to_response('file_upload_response.html',
                                          {'response': json.dumps({
                    'message': 'Certificate uploaded successfully! <a href="%s">View Certificate</a>'
                        % reverse('crits.certificates.views.certificate_details',
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
def remove_certificate(request, md5):
    """
    Remove a Certificate from CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param md5: The MD5 of the Certificate.
    :type md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    result = delete_cert(md5, '%s' % request.user.username)
    if result:
        return HttpResponseRedirect(reverse('crits.certificates.views.certificates_listing'))
    else:
        return render_to_response('error.html',
                                  {'error': "Could not delete certificate"})
