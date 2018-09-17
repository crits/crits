import json
import urllib

from django import forms
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import user_passes_test
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from crits.core import form_consts
from crits.core.user_tools import user_can_view_data
from crits.core.user_tools import user_sources
from crits.emails.email import Email
from crits.emails.forms import EmailYAMLForm, EmailOutlookForm, EmailEMLForm
from crits.emails.forms import EmailUploadForm, EmailRawUploadForm
from crits.emails.handlers import handle_email_fields, handle_yaml
from crits.emails.handlers import handle_eml, handle_msg
from crits.emails.handlers import update_email_header_value, handle_pasted_eml
from crits.emails.handlers import get_email_detail, generate_email_jtable
from crits.emails.handlers import generate_email_csv
from crits.emails.handlers import create_email_attachment, get_email_formatted
from crits.emails.handlers import create_indicator_from_header_field
from crits.samples.forms import UploadFileForm

from crits.vocabulary.acls import EmailACL

@user_passes_test(user_can_view_data)
def emails_listing(request,option=None):
    """
    Generate Email Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    user = request.user

    if not user.has_access_to(EmailACL.READ):
        return render(request, 'error.html',
                                  {'error':'User does not have permission to delete email.'})

    if option == "csv":
        return generate_email_csv(request)
    return generate_email_jtable(request, option)


@user_passes_test(user_can_view_data)
def email_search(request):
    """
    Generate email search results.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    query = {}
    query[request.GET.get('search_type',
                          '')]=request.GET.get('q',
                                               '').strip()
    return HttpResponseRedirect(reverse('crits-emails-views-emails_listing')
                                + "?%s" % urllib.urlencode(query))


@user_passes_test(user_can_view_data)
def email_del(request, email_id):
    """
    Delete an email.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param email_id: The ObjectId of the email to delete.
    :type email_id: str
    :returns: :class:`django.http.HttpResponse`
    """
    user = request.user

    email = Email.objects(id=email_id).first()
    if not user.has_access_to(EmailACL.DELETE):
        return render(request, 'error.html',
                                  {'error':'User does not have permission to delete email.'})
    if not email:
        return render(request, 'error.html', {'error': "Could not delete email."})

    email.delete(username=request.user.username)
    return HttpResponseRedirect(reverse('crits-emails-views-emails_listing'))


@user_passes_test(user_can_view_data)
def upload_attach(request, email_id):
    """
    Upload an attachment for an email.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param email_id: The ObjectId of the email to upload attachment for.
    :type email_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    redirect = reverse('crits-emails-views-email_detail', args=[email_id])
    user = request.user

    if request.method != 'POST':
        return HttpResponseRedirect(redirect)

    file_form = UploadFileForm(request.user, request.POST, request.FILES)
    json_reply = {'success': False}

    if not file_form.is_valid():
        file_form.fields['related_md5_event'].widget = forms.HiddenInput() #hide field so it doesn't reappear
        json_reply['form'] = file_form.as_table()
        return render(request, 'file_upload_response.html', {'response': json.dumps(json_reply)})

    if not user.has_access_to(EmailACL.ADD_ATTACHMENT):
        json_reply['message'] = "User does not have permission to upload attachment."
        return render(request, 'file_upload_response.html',
                                  {'response': json.dumps(json_reply)})


    analyst = request.user.username
    users_sources = user_sources(analyst)
    method = file_form.cleaned_data['method'] or "Add to Email"
    bucket_list = file_form.cleaned_data.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
    ticket = file_form.cleaned_data.get(form_consts.Common.TICKET_VARIABLE_NAME)
    email_addr = None


    if request.POST.get('email'):
        email_addr = request.user.email
    email = Email.objects(id=email_id,
                          source__name__in=users_sources).first()
    if not email:
        json_reply['message'] = "Could not find email."
        return render(request, 'file_upload_response.html', {'response': json.dumps(json_reply)})

    result = create_email_attachment(email,
                                     file_form,
                                     analyst,
                                     file_form.cleaned_data['source'],
                                     method,
                                     file_form.cleaned_data['reference'],
                                     file_form.cleaned_data['campaign'],
                                     file_form.cleaned_data['confidence'],
                                     bucket_list,
                                     ticket,
                                     request.FILES.get('filedata'),
                                     request.POST.get('filename'),
                                     request.POST.get('md5'),
                                     email_addr,
                                     file_form.cleaned_data['inherit_sources'])

    # If successful, tell the browser to redirect back to this email.
    if result['success']:
        result['redirect_url'] = redirect
    return render(request, 'file_upload_response.html', {'response': json.dumps(result)})


@user_passes_test(user_can_view_data)
def email_fields_add(request):
    """
    Upload an email using fields. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    fields_form = EmailUploadForm(request.user, request.POST)
    user = request.user
    json_reply = {
                   'form': fields_form.as_table(),
                   'success': False
                 }

    if request.method != "POST":
        message = "Must submit via POST"
    else:
        if not fields_form.is_valid():
            message = "Form is invalid."
        elif not user.has_access_to(EmailACL.WRITE):
            message = "User does not have permission to add email."
        else:
            form_data= fields_form.cleaned_data
            result = handle_email_fields(form_data,
                                         user,
                                         "Fields Upload",
                                         form_data['related_id'],
                                         form_data['related_type'],
                                         form_data['relationship_type'])

            if result['status']:
                redirect = reverse('crits-emails-views-email_detail',
                                   args=[result['object'].id])
                if not request.is_ajax():
                    return HttpResponseRedirect(redirect)
                json_reply['success'] = True
                del json_reply['form']
                message = 'Email uploaded successfully'
                if result.get('reason'):
                    message += ', but %s' % result['reason']
                message += ('. <a href="%s">View email.</a>' % redirect)
            else:
                message = result['reason']

    if request.is_ajax():
        json_reply['message'] = message
        return HttpResponse(json.dumps(json_reply),
                            content_type="application/json")
    else:
        return render(request, 'error.html', {'error': message})


@user_passes_test(user_can_view_data)
def email_yaml_add(request, email_id=None):
    """
    Upload an email using YAML. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param email_id: The ObjectId of an existing email to update.
    :type email_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    yaml_form = EmailYAMLForm(request.user, request.POST)
    user = request.user
    json_reply = {
                   'form': yaml_form.as_table(),
                   'success': False
                 }

    if request.method != "POST":
        message = "Must submit via POST"
    else:
        if not yaml_form.is_valid():
            message = "Form is invalid."
        elif not user.has_access_to(EmailACL.WRITE):
            message = "User does not have permission to add email."
        else:
            form_data = yaml_form.cleaned_data
            method = "YAML Upload"
            if form_data['source_method']:
                method = method + " - " + form_data['source_method']

            result = handle_yaml(form_data['yaml_data'],
                                 form_data['source_name'],
                                 form_data['source_reference'],
                                 method,
                                 form_data['source_tlp'],
                                 user,
                                 email_id,
                                 form_data['save_unsupported'],
                                 form_data['campaign'],
                                 form_data['campaign_confidence'],
                                 form_data['bucket_list'],
                                 form_data['ticket'],
                                 form_data['related_id'],
                                 form_data['related_type'],
                                 form_data['relationship_type'])

            if result['status']:
                redirect = reverse('crits-emails-views-email_detail',
                                   args=[result['object'].id])
                if not request.is_ajax():
                    return HttpResponseRedirect(redirect)
                json_reply['success'] = True
                message = 'Email uploaded successfully'
                if result.get('reason'):
                    message += ', but %s' % result['reason']
                message += ('. <a href="%s">View email.</a>' % redirect)
            else:
                message = result['reason']

    if request.is_ajax():
        json_reply['message'] = message
        return HttpResponse(json.dumps(json_reply),
                            content_type="application/json")
    else:
        return render(request, 'error.html', {'error': message})


@user_passes_test(user_can_view_data)
def email_raw_add(request):
    """
    Upload an email using Raw. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    raw_form = EmailRawUploadForm(request.user, request.POST)
    user = request.user

    json_reply = {
                   'form': raw_form.as_table(),
                   'success': False
                 }

    if request.method != "POST":
        message = "Must submit via POST"
    else:
        if not raw_form.is_valid():
            message = "Form is invalid."
        elif not user.has_access_to(EmailACL.WRITE):
            message = "User does not have permission to add email."
        else:
            form_data = raw_form.cleaned_data
            method = "Raw Upload"
            if form_data['source_method']:
                method = method + " - " + form_data['source_method']

            result = handle_pasted_eml(form_data['raw_email'],
                                       form_data['source_name'],
                                       form_data['source_reference'],
                                       form_data['source_method'],
                                       form_data['source_tlp'],
                                       user,
                                       form_data['campaign'],
                                       form_data['campaign_confidence'],
                                       form_data['bucket_list'],
                                       form_data['ticket'],
                                       form_data['related_id'],
                                       form_data['related_type'],
                                       form_data['relationship_type'])

            if result['status']:
                redirect = reverse('crits-emails-views-email_detail',
                                   args=[result['object'].id])
                if not request.is_ajax():
                    return HttpResponseRedirect(redirect)
                json_reply['success'] = True
                del json_reply['form']
                message = 'Email uploaded successfully'
                if result.get('reason'):
                    message += ', but %s' % result['reason']
                message += ('. <a href="%s">View email.</a>' % redirect)
            else:
                message = result['reason']


    if request.is_ajax():
        json_reply['message'] = message
        return HttpResponse(json.dumps(json_reply),
                            content_type="application/json")
    else:
        return render(request, 'error.html', {'error': message})


@user_passes_test(user_can_view_data)
def email_eml_add(request):
    """
    Upload an email using EML.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    eml_form = EmailEMLForm(request.user, request.POST, request.FILES)
    user = request.user

    json_reply = {
                   'form': eml_form.as_table(),
                   'success': False
                 }

    if request.method != "POST":
        message = "Must submit via POST."
    else:
        if not eml_form.is_valid():
            message = "Form is invalid."
        elif not user.has_access_to(EmailACL.WRITE):
            message = "User does not have permission to add email."

        else:
            form_data = eml_form.cleaned_data
            data = ''
            for chunk in request.FILES['filedata']:
                data += chunk

            method = "EML Upload"
            if form_data['source_method']:
                method = method + " - " + form_data['source_method']

            result = handle_eml(data,
                                form_data['source_name'],
                                form_data['source_reference'],
                                method,
                                form_data['source_tlp'],
                                user,
                                form_data['campaign'],
                                form_data['campaign_confidence'],
                                form_data['bucket_list'],
                                form_data['ticket'],
                                form_data['related_id'],
                                form_data['related_type'],
                                form_data['relationship_type'])

            if result['status']:
                redirect = reverse('crits-emails-views-email_detail',
                                   args=[result['object'].id])
                json_reply['success'] = True
                message = 'Email uploaded successfully'
                if result.get('reason'):
                    message += ', but %s' % result['reason']
                message += ('. <a href="%s">View email.</a>' % redirect)
            else:
                message = result['reason']

    json_reply['message'] = message
    return render(request, 'file_upload_response.html', {'response': json.dumps(json_reply)})


@user_passes_test(user_can_view_data)
def email_outlook_add(request):
    """
    Provides upload capability for Outlook .msg files (OLE2.0 format using
    Compound File Streams). This function will import the email into CRITs and
    upload any attachments as samples

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    outlook_form = EmailOutlookForm(request.user, request.POST, request.FILES)
    user = request.user
    json_reply = {
        'form': outlook_form.as_table(),
        'success': False
        }

    if request.method != "POST":
        message = "Must submit via POST."
    else:
        if not outlook_form.is_valid():
            message = "Form is invalid."
        elif not user.has_access_to(EmailACL.WRITE):
            message = "User does not have permission to add email."
        else:
            form_data = outlook_form.cleaned_data
            method = "Outlook MSG Upload"
            if form_data['source_method']:
                method = method + " - " + form_data['source_method']

            result = handle_msg(request.FILES['msg_file'],
                                form_data['source_name'],
                                form_data['source_reference'],
                                form_data['source_method'],
                                form_data['source_tlp'],
                                user,
                                form_data['password'],
                                form_data['campaign'],
                                form_data['campaign_confidence'],
                                form_data['bucket_list'],
                                form_data['ticket'],
                                form_data['related_id'],
                                form_data['related_type'],
                                form_data['relationship_type'])

            if result['status']:
                redirect = reverse('crits-emails-views-email_detail',
                                   args=[result['obj_id']])
                json_reply['success'] = True
                message = 'Email uploaded successfully'
                if result.get('reason'):
                    message += ', but %s' % result['reason']
                message += ('. <a href="%s">View email.</a>' % redirect)
                if 'message' in result:
                    message += "<br />Attachments:<br />%s" % result['message']
            else:
                message = result['reason']

    json_reply['message'] = message
    return render(request, 'file_upload_response.html',
                  {'response': json.dumps(json_reply)})


@user_passes_test(user_can_view_data)
def email_detail(request, email_id):
    """
    Generate the Email detail page.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param email_id: The ObjectId of the email to get details for.
    :type email_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    template = 'email_detail.html'
    user = request.user
    if not user.has_access_to(EmailACL.READ):
        return render(request, 'error.html',
                                  {'error':'User does not have permission to view email.'})
    if request.method == "GET" and request.is_ajax():
        return get_email_formatted(email_id,
                                   user.username,
                                   request.GET.get("format", "json"))
    (new_template, args) = get_email_detail(email_id, user)
    if new_template:
        template = new_template
    return render(request, template, args)


@user_passes_test(user_can_view_data)
def indicator_from_header_field(request, email_id):
    """
    Create an indicator from a header field. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param email_id: The ObjectId of the email to get the header from.
    :type email_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        if 'type' in request.POST:
            header_field = request.POST.get('field')
            header_type = request.POST.get('type')
            analyst = request.user.username
            sources = user_sources(analyst)
            email = Email.objects(id=email_id,
                                  source__name__in=sources).first()
            if not email:
                result = {
                    'success':  False,
                    'message':  "Could not find email."
                }
            else:
                result = create_indicator_from_header_field(email,
                                                            header_field,
                                                            header_type,
                                                            analyst,
                                                            request)
        else:
            result = {
                'success':  False,
                'message':  "Type is a required value."
            }
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        return render(request, 'error.html', {'error': "Expected AJAX POST"})


@user_passes_test(user_can_view_data)
def update_header_value(request, email_id):
    """
    Update the header value of an email. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param email_id: The ObjectId of the email to update a header for.
    :type email_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        type_ = request.POST.get('type', None)
        value = request.POST.get('value', None)
        analyst = request.user.username
        result = update_email_header_value(email_id,
                                           type_,
                                           value,
                                           analyst)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        return render(request, 'error.html', {'error': "Expected AJAX POST"})
