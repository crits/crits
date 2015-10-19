import json

from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.core.handlers import get_item_names
from crits.core.user_tools import user_can_view_data
from crits.core.user_tools import user_is_admin
from crits.signatures.forms import UploadSignatureForm
from crits.signatures.forms import NewSignatureTypeForm
from crits.signatures.handlers import update_signature_type
from crits.signatures.handlers import handle_signature_file
from crits.signatures.handlers import delete_signature, get_signature_details
from crits.signatures.handlers import generate_signature_jtable
from crits.signatures.handlers import generate_signature_csv, new_inline_comment
from crits.signatures.handlers import generate_inline_comments
from crits.signatures.handlers import generate_signature_versions
from crits.signatures.handlers import get_id_from_link_and_version
from crits.signatures.handlers import add_new_signature_type, new_highlight
from crits.signatures.handlers import update_signature_highlight_comment
from crits.signatures.handlers import delete_highlight
from crits.signatures.handlers import update_signature_highlight_date
from crits.signatures.signature import SignatureType

@user_passes_test(user_can_view_data)
def signatures_listing(request,option=None):
    """
    Generate Signature Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_signature_csv(request)
    return generate_signature_jtable(request, option)

@user_passes_test(user_can_view_data)
def set_signature_type(request, _id):
    """
    Set the Signature datatype. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Signature.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        data_type = request.POST['data_type']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_signature_type(_id,
                                                            data_type,
                                                            analyst)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def set_signature_highlight_comment(request, _id):
    """
    Set a highlight comment in Signature. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Signature.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        comment = request.POST['comment']
        line = request.POST['line']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_signature_highlight_comment(_id,
                                                                         comment,
                                                                         line,
                                                                         analyst)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def set_signature_highlight_date(request, _id):
    """
    Set a highlight date in Signature. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Signature.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        date = request.POST['date']
        line = request.POST['line']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_signature_highlight_date(_id,
                                                                      date,
                                                                      line,
                                                                      analyst)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def add_inline_comment(request, _id):
    """
    Add an inline comment to Signature. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Signature.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        comment = request.POST['comment']
        analyst = request.user.username
        line_num = request.GET.get('line', 1)
        return HttpResponse(json.dumps(new_inline_comment(_id,
                                                          comment,
                                                          line_num,
                                                          analyst)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def add_highlight(request, _id):
    """
    Set a line as highlighted for Signature. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Signature.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        analyst = request.user.username
        line_num = request.POST.get('line', 1)
        line_data = request.POST.get('line_data', None)
        return HttpResponse(json.dumps(new_highlight(_id,
                                                     line_num,
                                                     line_data,
                                                     analyst)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def remove_highlight(request, _id):
    """
    Remove a line highlight from Signature. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Signature.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        analyst = request.user.username
        line_num = request.POST.get('line', 1)
        return HttpResponse(json.dumps(delete_highlight(_id,
                                                        line_num,
                                                        analyst)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def get_inline_comments(request, _id):
    """
    Get inline comments for Signature. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Signature.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        return HttpResponse(json.dumps(generate_inline_comments(_id)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def get_signature_versions(request, _id):
    """
    Get a list of versions for Signature. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Signature.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        return HttpResponse(json.dumps(generate_signature_versions(_id)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def signature_detail(request, _id):
    """
    Generate Signature details page.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Signature.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    template = 'signature_detail.html'
    analyst = request.user.username
    (new_template, args) = get_signature_details(_id, analyst)
    if new_template:
        template = new_template
    return render_to_response(template,
                              args,
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def details_by_link(request, link):
    """
    Generate Signature details page by link.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param link: The LinkId of the Signature.
    :type link: str
    :returns: :class:`django.http.HttpResponse`
    """

    version = request.GET.get('version', 1)
    return signature_detail(request,
                            get_id_from_link_and_version(link, version))

@user_passes_test(user_can_view_data)
def upload_signature(request, link_id=None):
    """
    Upload new Signature to CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param link_id: The LinkId of Signature if this is a new version upload.
    :type link_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        form = UploadSignatureForm(request.user, request.POST)
        if form.is_valid():
            data = request.POST.get('data', None)
            source = form.cleaned_data.get('source')
            user = request.user.username
            description = form.cleaned_data.get('description', '')
            title = form.cleaned_data.get('title', None)
            data_type = form.cleaned_data.get('data_type', None)
            copy_rels = request.POST.get('copy_relationships', False)
            link_id = link_id
            bucket_list = form.cleaned_data.get('bucket_list')
            ticket = form.cleaned_data.get('ticket')
            method = form.cleaned_data.get('method', '') or 'Upload'
            reference = form.cleaned_data.get('reference', '')
            status = handle_signature_file(data, source, user,
                                          description, title, data_type,
                                          link_id,
                                          method=method,
                                          reference=reference,
                                          copy_rels=copy_rels,
                                          bucket_list=bucket_list,
                                          ticket=ticket)
            if status['success']:
                jdump = json.dumps({
                    'message': 'signature uploaded successfully! <a href="%s">View signature</a>'
                    % reverse('crits.signatures.views.signature_detail',
                              args=[status['_id']]), 'success': True})
                return HttpResponse(jdump, mimetype="application/json")

            else:
                jdump = json.dumps({'success': False,
                                    'message': status['message']})
                return HttpResponse(jdump, mimetype="application/json")

        else:
            jdump = json.dumps({'success': False,
                                'form': form.as_table()})
            return HttpResponse(jdump, mimetype="application/json")

    else:
        return render_to_response('error.html',
                                  {'error': "Expected POST."},
                                  RequestContext(request))

@user_passes_test(user_is_admin)
def remove_signature(request, _id):
    """
    Remove Signature from CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Signature to remove.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    result = delete_signature(_id, '%s' % request.user.username)
    if result:
        return HttpResponseRedirect(reverse('crits.signatures.views.signatures_listing'))
    else:
        return render_to_response('error.html',
                                  {'error': "Could not delete signature"})

@user_passes_test(user_can_view_data)
def new_signature_type(request):
    """
    Add a new Signature datatype to CRITs. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        form = NewSignatureTypeForm(request.POST)
        analyst = request.user.username
        if form.is_valid():
            result = add_new_signature_type(form.cleaned_data['data_type'],
                                           analyst)
            if result:
                message = {'message': '<div>Signature Type added successfully!</div>',
                           'success': True}
            else:
                message = {'message': '<div>Signature Type addition failed!</div>',
                           'success': False}
        else:
            message = {'form': form.as_table()}
        return HttpResponse(json.dumps(message),
                            mimetype="application/json")
    return render_to_response('error.html',
                              {'error':'Expected AJAX POST'})


@user_passes_test(user_can_view_data)
def get_signature_type_dropdown(request):
    """
    Generate Signature datetypes dropdown information. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        dt_types = get_item_names(SignatureType)
        dt_final = []
        for dt in dt_types:
            dt_final.append(dt.name)
            result = {'data': dt_final}
        return HttpResponse(json.dumps(result),
                            mimetype="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {'error': error},
                                  RequestContext(request))
