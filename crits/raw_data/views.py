import json

from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.core.handlers import get_item_names
from crits.core.user_tools import user_can_view_data
from crits.core.user_tools import user_is_admin
from crits.raw_data.forms import UploadRawDataFileForm, UploadRawDataForm
from crits.raw_data.forms import NewRawDataTypeForm
from crits.raw_data.handlers import update_raw_data_tool_details
from crits.raw_data.handlers import update_raw_data_tool_name
from crits.raw_data.handlers import update_raw_data_type
from crits.raw_data.handlers import handle_raw_data_file
from crits.raw_data.handlers import delete_raw_data, get_raw_data_details
from crits.raw_data.handlers import generate_raw_data_jtable
from crits.raw_data.handlers import generate_raw_data_csv, new_inline_comment
from crits.raw_data.handlers import generate_inline_comments
from crits.raw_data.handlers import generate_raw_data_versions
from crits.raw_data.handlers import get_id_from_link_and_version
from crits.raw_data.handlers import add_new_raw_data_type, new_highlight
from crits.raw_data.handlers import update_raw_data_highlight_comment
from crits.raw_data.handlers import delete_highlight
from crits.raw_data.handlers import update_raw_data_highlight_date
from crits.raw_data.raw_data import RawDataType

@user_passes_test(user_can_view_data)
def raw_data_listing(request,option=None):
    """
    Generate RawData Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_raw_data_csv(request)
    return generate_raw_data_jtable(request, option)

@user_passes_test(user_can_view_data)
def set_raw_data_tool_details(request, _id):
    """
    Set the RawData tool details. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the RawData.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        details = request.POST['details']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_raw_data_tool_details(_id,
                                                               details,
                                                               analyst)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def set_raw_data_tool_name(request, _id):
    """
    Set the RawData tool name. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the RawData.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        name = request.POST['name']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_raw_data_tool_name(_id,
                                                               name,
                                                               analyst)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def set_raw_data_type(request, _id):
    """
    Set the RawData datatype. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the RawData.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        data_type = request.POST['data_type']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_raw_data_type(_id,
                                                            data_type,
                                                            analyst)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def set_raw_data_highlight_comment(request, _id):
    """
    Set a highlight comment in RawData. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the RawData.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        comment = request.POST['comment']
        line = request.POST['line']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_raw_data_highlight_comment(_id,
                                                                         comment,
                                                                         line,
                                                                         analyst)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def set_raw_data_highlight_date(request, _id):
    """
    Set a highlight date in RawData. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the RawData.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        date = request.POST['date']
        line = request.POST['line']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_raw_data_highlight_date(_id,
                                                                      date,
                                                                      line,
                                                                      analyst)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def add_inline_comment(request, _id):
    """
    Add an inline comment to RawData. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the RawData.
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
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def add_highlight(request, _id):
    """
    Set a line as highlighted for RawData. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the RawData.
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
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def remove_highlight(request, _id):
    """
    Remove a line highlight from RawData. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the RawData.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        analyst = request.user.username
        line_num = request.POST.get('line', 1)
        return HttpResponse(json.dumps(delete_highlight(_id,
                                                        line_num,
                                                        analyst)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def get_inline_comments(request, _id):
    """
    Get inline comments for RawData. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the RawData.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        return HttpResponse(json.dumps(generate_inline_comments(_id)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def get_raw_data_versions(request, _id):
    """
    Get a list of versions for RawData. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the RawData.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        return HttpResponse(json.dumps(generate_raw_data_versions(_id)),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def raw_data_details(request, _id):
    """
    Generate RawData details page.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the RawData.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    template = 'raw_data_details.html'
    analyst = request.user.username
    (new_template, args) = get_raw_data_details(_id, analyst)
    if new_template:
        template = new_template
    return render_to_response(template,
                              args,
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def details_by_link(request, link):
    """
    Generate RawData details page by link.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param link: The LinkId of the RawData.
    :type link: str
    :returns: :class:`django.http.HttpResponse`
    """

    version = request.GET.get('version', 1)
    return raw_data_details(request,
                            get_id_from_link_and_version(link, version))

@user_passes_test(user_can_view_data)
def upload_raw_data(request, link_id=None):
    """
    Upload new RawData to CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param link_id: The LinkId of RawData if this is a new version upload.
    :type link_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        if 'filedata' in request.FILES:
            form = UploadRawDataFileForm(request.user,
                                         request.POST,
                                         request.FILES)
            filedata = request.FILES['filedata']
            data = filedata.read() # XXX: Should be using chunks here.
            has_file = True
        else:
            form = UploadRawDataForm(request.user,request.POST)
            data = request.POST.get('data', None)
            has_file = False
        if form.is_valid():
            source = form.cleaned_data.get('source')
            user = request.user.username
            description = form.cleaned_data.get('description', '')
            title = form.cleaned_data.get('title', None)
            tool_name = form.cleaned_data.get('tool_name', '')
            tool_version = form.cleaned_data.get('tool_version', '')
            tool_details = form.cleaned_data.get('tool_details', '')
            data_type = form.cleaned_data.get('data_type', None)
            copy_rels = request.POST.get('copy_relationships', False)
            link_id = link_id
            bucket_list = form.cleaned_data.get('bucket_list')
            ticket = form.cleaned_data.get('ticket')
            method = form.cleaned_data.get('method', '') or 'Upload'
            reference = form.cleaned_data.get('reference', '')
            status = handle_raw_data_file(data, source, user,
                                          description, title, data_type,
                                          tool_name, tool_version, tool_details,
                                          link_id,
                                          method=method,
                                          reference=reference,
                                          copy_rels=copy_rels,
                                          bucket_list=bucket_list,
                                          ticket=ticket)
            if status['success']:
                jdump = json.dumps({
                    'message': 'raw_data uploaded successfully! <a href="%s">View raw_data</a>'
                    % reverse('crits.raw_data.views.raw_data_details',
                              args=[status['_id']]), 'success': True})
                if not has_file:
                    return HttpResponse(jdump, content_type="application/json")
                return render_to_response('file_upload_response.html',
                                          {'response': jdump},
                                          RequestContext(request))
            else:
                jdump = json.dumps({'success': False,
                                    'message': status['message']})
                if not has_file:
                    return HttpResponse(jdump, content_type="application/json")
                return render_to_response('file_upload_response.html',
                                          {'response': jdump},
                                          RequestContext(request))
        else:
            jdump = json.dumps({'success': False,
                                'form': form.as_table()})
            if not has_file:
                return HttpResponse(jdump, content_type="application/json")
            return render_to_response('file_upload_response.html',
                                      {'response': jdump},
                                      RequestContext(request))
    else:
        return render_to_response('error.html',
                                  {'error': "Expected POST."},
                                  RequestContext(request))

@user_passes_test(user_is_admin)
def remove_raw_data(request, _id):
    """
    Remove RawData from CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the RawData to remove.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    result = delete_raw_data(_id, '%s' % request.user.username)
    if result:
        return HttpResponseRedirect(reverse('crits.raw_data.views.raw_data_listing'))
    else:
        return render_to_response('error.html',
                                  {'error': "Could not delete raw_data"})

@user_passes_test(user_can_view_data)
def new_raw_data_type(request):
    """
    Add a new RawData datatype to CRITs. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        form = NewRawDataTypeForm(request.POST)
        analyst = request.user.username
        if form.is_valid():
            result = add_new_raw_data_type(form.cleaned_data['data_type'],
                                           analyst)
            if result:
                message = {'message': '<div>Raw Data Type added successfully!</div>',
                           'success': True}
            else:
                message = {'message': '<div>Raw Data Type addition failed!</div>',
                           'success': False}
        else:
            message = {'form': form.as_table()}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")
    return render_to_response('error.html',
                              {'error':'Expected AJAX POST'})


@user_passes_test(user_can_view_data)
def get_raw_data_type_dropdown(request):
    """
    Generate RawData datetypes dropdown information. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        dt_types = get_item_names(RawDataType)
        dt_final = []
        for dt in dt_types:
            dt_final.append(dt.name)
            result = {'data': dt_final}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {'error': error},
                                  RequestContext(request))
