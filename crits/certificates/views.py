import json

from django.contrib.auth.decorators import user_passes_test
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from crits.core import form_consts
from crits.core.user_tools import user_can_view_data
from crits.core.data_tools import json_handler

from crits.certificates.forms import UploadCertificateForm
from crits.certificates.handlers import handle_cert_file
from crits.certificates.handlers import delete_cert, get_certificate_details
from crits.certificates.handlers import generate_cert_jtable, generate_cert_csv

from crits.vocabulary.acls import CertificateACL

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
    request.user._setup()
    user = request.user
    if user.has_access_to(CertificateACL.READ):
        if option == "csv":
            return generate_cert_csv(request)
        elif option== "jtdelete" and not user.has_access_to(CertificateACL.DELETE):
            result = {'sucess':False,
                      'message':'User does not have permission to delete Certificate.'}
            return HttpResponse(json.dumps(result,
                                           default=json_handler),
                                content_type="application/json")
        return generate_cert_jtable(request, option)
    else:
        return render(request, "error.html",
                                  {'error': 'User does not have permission to view Certificate listing.'})

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
    request.user._setup()

    template = 'certificate_details.html'
    user = request.user
    if user.has_access_to(CertificateACL.READ):
        (new_template, args) = get_certificate_details(md5, user)
        if new_template:
            template = new_template
        return render(request, template,
                                  args)
    else:
        return render(request, "error.html",
                                  {'error': 'User does not have permission to view Certificate.'})

@user_passes_test(user_can_view_data)
def upload_certificate(request):
    """
    Add a new Certificate to CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """
    user = request.user

    if request.method == 'POST':
        form = UploadCertificateForm(user, request.POST, request.FILES)
        if form.is_valid():
            if user.has_access_to(CertificateACL.WRITE):
                filedata = request.FILES['filedata']
                filename = filedata.name
                data = filedata.read() # XXX: Should be using chunks here.
                source = form.cleaned_data.get('source_name')
                description = form.cleaned_data.get('description', '')
                related = form.cleaned_data.get('related_id', '')
                related_type = form.cleaned_data.get('related_type', '')
                relationship_type = form.cleaned_data.get('relationship_type','')
                bucket_list = form.cleaned_data.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
                ticket = form.cleaned_data.get(form_consts.Common.TICKET_VARIABLE_NAME)
                method = form.cleaned_data.get('source_method', '') or 'Upload'
                reference = form.cleaned_data.get('source_reference', '')
                tlp = form.cleaned_data.get('source_tlp', None)
                status = handle_cert_file(filename, data, source, user, description,
                                          related_id=related, related_type=related_type,
                                          relationship_type=relationship_type, method=method,
                                          reference=reference, tlp=tlp, bucket_list=bucket_list,
                                          ticket=ticket)
            else:
                status = {'success':False,
                          'message':'User does not have permission to add Certificate.'}

            if status['success']:
                return render(request, 'file_upload_response.html',
                                          {'response': json.dumps({
                    'message': 'Certificate uploaded successfully! <a href="%s">View Certificate</a>'
                        % reverse('crits-certificates-views-certificate_details',
                                  args=[status['md5']]), 'success': True})},
                                          )
            else:
                return render(request, 'file_upload_response.html', {'response': json.dumps({ 'success': False})})
        else:
            return render(request, 'file_upload_response.html', {'response': json.dumps({'success': False})})
    else:
        return render(request, 'error.html', {'error': "Expected POST."})

@user_passes_test(user_can_view_data)
def remove_certificate(request, md5):
    """
    Remove a Certificate from CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param md5: The MD5 of the Certificate.
    :type md5: str
    :returns: :class:`django.http.HttpResponse`
    """
    user = request.user
    if user.has_access_to(CertificateACL.DELETE):
        result = delete_cert(md5, '%s' % user)
    else:
        result = {'success':False,
                  'message':'User does not have permission to delete certificate.'}
    if result:
        return HttpResponseRedirect(reverse('crits-certificates-views-certificates_listing'))
    else:
        return render(request, 'error.html',
                                  {'error': "Could not delete certificate"})
