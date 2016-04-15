import json

from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.core import form_consts
from crits.core.crits_mongoengine import EmbeddedCampaign
from crits.core.data_tools import json_handler, make_ascii_strings
from crits.core.data_tools import make_unicode_strings, make_hex, xor_search
from crits.core.data_tools import xor_string, make_stackstrings
from crits.core.exceptions import ZipFileError
from crits.core.handsontable_tools import form_to_dict
from crits.core.class_mapper import class_from_id
from crits.core.user_tools import user_can_view_data, user_is_admin
from crits.core.user_tools import get_user_organization
from crits.objects.forms import AddObjectForm
from crits.samples.forms import UploadFileForm, XORSearchForm
from crits.samples.forms import UnzipSampleForm
from crits.samples.handlers import handle_uploaded_file, mail_sample
from crits.samples.handlers import generate_yarahit_jtable
from crits.samples.handlers import delete_sample, handle_unzip_file
from crits.samples.handlers import get_source_counts
from crits.samples.handlers import get_sample_details
from crits.samples.handlers import generate_sample_jtable
from crits.samples.handlers import generate_sample_csv, process_bulk_add_md5_sample
from crits.samples.handlers import update_sample_filename, modify_sample_filenames
from crits.samples.sample import Sample
from crits.stats.handlers import generate_sources


@user_passes_test(user_can_view_data)
def detail(request, sample_md5):
    """
    Generate the sample details page.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param sample_md5: The MD5 of the Sample.
    :type sample_md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    format_ = request.GET.get('format', None)
    template = "samples_detail.html"
    (new_template, args) = get_sample_details(sample_md5,
                                              request.user.username,
                                              format_)
    if new_template:
        template = new_template
    if template == "yaml":
        return HttpResponse(args, content_type="text/plain")
    elif template == "json":
        return HttpResponse(json.dumps(args), content_type="application/json")
    return render_to_response(template,
                              args,
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def samples_listing(request,option=None):
    """
    Generate Samples Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_sample_csv(request)
    return generate_sample_jtable(request, option)

@user_passes_test(user_can_view_data)
def yarahits_listing(request,option=None):
    """
    Generate YaraHits Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    return generate_yarahit_jtable(request, option)

@user_passes_test(user_can_view_data)
def view_upload_list(request, filename, md5s):
    """
    View a list of uploaded files.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param filename: The name of the original file that was uploaded.
    :type filename: str
    :param md5s: The MD5s of the files that were uploaded.
    :type md5s: str
    :returns: :class:`django.http.HttpResponse`
    """

    #convert md5s list from unicode to list
    while md5s.endswith('/'):
        md5s = md5s[:-1]
    import ast
    md5s = ast.literal_eval(md5s)
    return render_to_response('samples_uploadList.html',
                              {'sample_md5': md5s,
                               'archivename': filename},
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def bulk_add_md5_sample(request):
    """
    Bulk add samples via a bulk upload form.

    Args:
        request: The Django context which contains information about the
            session and key/value pairs for the bulk add request

    Returns:
        If the request is not a POST and not a Ajax call then:
            Returns a rendered HTML form for a bulk add of domains
        If the request is a POST and a Ajax call then:
            Returns a response that contains information about the
            status of the bulk add. This may include information
            such as items that failed or successfully added. This may
            also contain helpful status messages about each operation.
    """

    formdict = form_to_dict(UploadFileForm(request.user, request.POST, request.FILES))
    objectformdict = form_to_dict(AddObjectForm(request.user))

    if request.method == "POST" and request.is_ajax():
        response = process_bulk_add_md5_sample(request, formdict);

        return HttpResponse(json.dumps(response,
                            default=json_handler),
                            content_type="application/json")
    else:
        return render_to_response('bulk_add_default.html',
                                  {'formdict': formdict,
                                  'objectformdict': objectformdict,
                                  'title': "Bulk Add Samples",
                                  'table_name': 'sample',
                                  'local_validate_columns': [form_consts.Sample.MD5],
                                  'is_bulk_add_objects': True},
                                  RequestContext(request));

@user_passes_test(user_can_view_data)
def upload_file(request, related_md5=None):
    """
    Upload a new sample.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param related_md5: The MD5 of a related sample.
    :type related_md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        form = UploadFileForm(request.user, request.POST, request.FILES)
        email_errmsg = None
        if form.is_valid():
            response = {'success': False,
                        'message': 'Unknown error; unable to upload file.'}
            inherited_source = None
            backdoor = form.cleaned_data['backdoor']
            campaign = form.cleaned_data['campaign']
            confidence = form.cleaned_data['confidence']
            source = form.cleaned_data['source']
            method = form.cleaned_data['method']
            reference = form.cleaned_data['reference']
            analyst = request.user.username
            related_id = form.cleaned_data.get('related_id', None)
            related_type = form.cleaned_data.get('related_type', None)
            relationship_type = form.cleaned_data.get('relationship_type', None)


            if related_md5:
                reload_page = True
            else:
                reload_page = False
                related_md5 = form.cleaned_data['related_md5']

            if related_md5:
                related_sample = Sample.objects(md5=related_md5).first()
                if not related_sample:
                    response['message'] = ("Upload Failed. Unable to locate related sample. %s" % related_md5)
                    return render_to_response("file_upload_response.html",
                                              {'response': json.dumps(response)},
                                              RequestContext(request))
                # If selected, new sample inherits the campaigns of the related sample.
                if form.cleaned_data['inherit_campaigns']:
                    if campaign:
                        related_sample.campaign.append(EmbeddedCampaign(name=campaign, confidence=confidence, analyst=analyst))
                    campaign = related_sample.campaign
                # If selected, new sample inherits the sources of the related sample
                if form.cleaned_data['inherit_sources']:
                    inherited_source = related_sample.source

            elif related_id:
                related_obj = class_from_id(related_type, related_id)
                if not related_obj:
                    response['success'] = False
                    response['message'] = ("Upload Failed. Unable to locate related Item")
                    return render_to_response("file_upload_response.html",{'response': json.dumps(response)}, RequestContext(request))

                else:
                    if form.cleaned_data['inherit_campaigns']:
                        if  campaign:
                            related_obj.campaign.append(EmbeddedCampaign(name=campaign, confidence=confidence, analyst=analyst))
                        campaign = related_obj.campaign

                    if form.cleaned_data['inherit_sources']:
                        inherited_source = related_obj.source

            backdoor_name = None
            backdoor_version = None
            if backdoor:
                backdoor = backdoor.split('|||')
                if len(backdoor) == 2:
                    (backdoor_name, backdoor_version) = backdoor[0], backdoor[1]

            try:
                if request.FILES:
                    result = handle_uploaded_file(
                        request.FILES['filedata'],
                        source,
                        method=method,
                        reference=reference,
                        file_format=form.cleaned_data['file_format'],
                        password=form.cleaned_data['password'],
                        user=analyst,
                        campaign=campaign,
                        confidence=confidence,
                        related_md5=related_md5,
                        related_id=related_id,
                        related_type=related_type,
                        relationship_type=relationship_type,
                        bucket_list=form.cleaned_data[form_consts.Common.BUCKET_LIST_VARIABLE_NAME],
                        ticket=form.cleaned_data[form_consts.Common.TICKET_VARIABLE_NAME],
                        inherited_source=inherited_source,
                        backdoor_name=backdoor_name,
                        backdoor_version=backdoor_version)
                else:
                    result = handle_uploaded_file(
                        None,
                        source,
                        method=method,
                        reference=reference,
                        file_format=form.cleaned_data['file_format'],
                        password=None,
                        user=analyst,
                        campaign=campaign,
                        confidence=confidence,
                        related_md5 = related_md5,
                        related_id=related_id,
                        related_type=related_type,
                        relationship_type=relationship_type,
                        filename=request.POST['filename'].strip(),
                        md5=request.POST['md5'].strip().lower(),
                        sha1=request.POST['sha1'].strip().lower(),
                        sha256=request.POST['sha256'].strip().lower(),
                        bucket_list=form.cleaned_data[form_consts.Common.BUCKET_LIST_VARIABLE_NAME],
                        ticket=form.cleaned_data[form_consts.Common.TICKET_VARIABLE_NAME],
                        inherited_source=inherited_source,
                        is_return_only_md5=False,
                        backdoor_name=backdoor_name,
                        backdoor_version=backdoor_version)

            except ZipFileError, zfe:
                return render_to_response('file_upload_response.html',
                                          {'response': json.dumps({'success': False,
                                                                   'message': zfe.value})},
                                          RequestContext(request))
            else:
                if len(result) > 1:
                    filedata = request.FILES['filedata']
                    message = ('<a href="%s">View Uploaded Samples.</a>'
                               % reverse('crits.samples.views.view_upload_list',
                                         args=[filedata.name, result]))
                    response = {'success': True,
                                'message': message }
                    md5_response = result
                elif len(result) == 1:
                    md5_response = None
                    if not request.FILES:
                        response['success'] = result[0].get('success', False)
                        if(response['success'] == False):
                            response['message'] = result[0].get('message', response.get('message'))
                        else:
                            md5_response = [result[0].get('object').md5]
                    else:
                        md5_response = [result[0]]
                        response['success'] = True

                    if md5_response != None:
                        response['message'] = ('File uploaded successfully. <a href="%s">View Sample.</a>'
                                               % reverse('crits.samples.views.detail',
                                                         args=md5_response))

                if response['success']:
                    if request.POST.get('email'):
                        for s in md5_response:
                            email_errmsg = mail_sample(s, [request.user.email])
                            if email_errmsg is not None:
                                msg = "<br>Error emailing sample %s: %s\n" % (s, email_errmsg)
                                response['message'] = response['message'] + msg
                    if reload_page:
                        response['redirect_url'] = reverse('crits.samples.views.detail', args=[related_md5])
                return render_to_response("file_upload_response.html",
                                          {'response': json.dumps(response)},
                                          RequestContext(request))
        else:
            if related_md5: #if this is a 'related' upload, hide field so it doesn't reappear
                form.fields['related_md5'].widget = forms.HiddenInput()
            return render_to_response('file_upload_response.html',
                                      {'response': json.dumps({'success': False,
                                                               'form': form.as_table()})},
                                      RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('crits.samples.views.samples_listing'))

@user_passes_test(user_can_view_data)
def strings(request, sample_md5):
    """
    Generate strings for a sample. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param sample_md5: The MD5 of the sample to use.
    :type sample_md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.is_ajax():
        strings_data = make_ascii_strings(md5=sample_md5)
        strings_data += make_unicode_strings(md5=sample_md5)
        result = {"strings": strings_data}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        return render_to_response('error.html',
                                  {'error': "Expected AJAX."},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def stackstrings(request, sample_md5):
    """
    Generate stack strings for a sample. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param sample_md5: The MD5 of the sample to use.
    :type sample_md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.is_ajax():
        strings = make_stackstrings(md5=sample_md5)
        result = {"strings": strings}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        return render_to_response('error.html',
                                  {'error': "Expected AJAX."},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def hex(request,sample_md5):
    """
    Generate hex for a sample. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param sample_md5: The MD5 of the sample to use.
    :type sample_md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.is_ajax():
        hex_data = make_hex(md5=sample_md5)
        result = {"strings": hex_data}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        return render_to_response('error.html',
                                  {'error': "Expected AJAX."},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def xor(request,sample_md5):
    """
    Generate xor results for a sample. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param sample_md5: The MD5 of the sample to use.
    :type sample_md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.is_ajax():
        key = request.GET.get('key')
        key = int(key)
        xor_data = xor_string(md5=sample_md5,
                              key=key)
        xor_data = make_ascii_strings(data=xor_data)
        result = {"strings": xor_data}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        return render_to_response('error.html',
                                  {'error': "Expected AJAX."},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def xor_searcher(request, sample_md5):
    """
    Generate xor search results for a sample. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param sample_md5: The MD5 of the sample to use.
    :type sample_md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        form = XORSearchForm(request.POST)
        if form.is_valid():
            try:
                string = request.POST['string']
            except:
                string = None
            try:
                if request.POST["skip_nulls"] == "on":
                    skip_nulls = 1
            except:
                skip_nulls = 0
            try:
                if request.POST["is_key"] == "on":
                    is_key = 1
            except:
                is_key = 0
            if is_key:
                try:
                    result = {"keys": [int(string)]}
                except:
                    result = {"keys": []}
            else:
                results = xor_search(md5=sample_md5,
                                    string=string,
                                     skip_nulls=skip_nulls)
                result = {"keys": results}
            return HttpResponse(json.dumps(result),
                                content_type="application/json")
        else:
            return render_to_response('error.html',
                                      {'error': "Invalid Form."},
                                      RequestContext(request))
    else:
        return render_to_response('error.html',
                                  {'error': "Expected AJAX POST."},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def unzip_sample(request, md5):
    """
    Unzip a sample.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param md5: The MD5 of the sample to use.
    :type md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST":
        form = UnzipSampleForm(request.POST)
        if form.is_valid():
            pwd = form.cleaned_data['password']
            try:
                handle_unzip_file(md5, user=request.user.username, password=pwd)
            except ZipFileError, zfe:
                return render_to_response('error.html',
                                          {'error' : zfe.value},
                                          RequestContext(request))
        return HttpResponseRedirect(reverse('crits.samples.views.detail',
                                            args=[md5]))
    else:
        return render_to_response('error.html',
                                  {'error': 'Expecting POST.'},
                                  RequestContext(request))


#TODO: convert to jtable
@user_passes_test(user_can_view_data)
def sources(request):
    """
    Get the sources list for samples.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    refresh = request.GET.get("refresh", "no")
    if refresh == "yes":
        generate_sources()
    sources_list = get_source_counts(request.user)
    return render_to_response('samples_sources.html',
                              {'sources': sources_list},
                              RequestContext(request))

@user_passes_test(user_is_admin)
def remove_sample(request, md5):
    """
    Remove a sample from CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param md5: The MD5 of the sample to remove.
    :type md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    result = delete_sample(md5, '%s' % request.user.username)
    if result:
        org = get_user_organization(request.user.username)
        return HttpResponseRedirect(reverse('crits.samples.views.samples_listing')
                                    +'?source=%s' % org)
    else:
        return render_to_response('error.html',
                                  {'error': "Could not delete sample"},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def set_sample_filename(request):
    """
    Set a Sample filename. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        filename = request.POST.get('filename', None)
        id_ = request.POST.get('id', None)
        analyst = request.user.username
        return HttpResponse(json.dumps(update_sample_filename(id_,
                                                              filename,
                                                              analyst)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def set_sample_filenames(request):
    """
    Set Sample filenames. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        tags = request.POST.get('tags', "").split(",")
        id_ = request.POST.get('id', None)
        return HttpResponse(json.dumps(modify_sample_filenames(id_,
                                                               tags,
                                                               request.user.username)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html", {"error" : error },
                                  RequestContext(request))
