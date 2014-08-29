import json
from hashlib import md5

from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.core.handlers import get_item_names
from crits.core.user_tools import user_can_view_data
from crits.core.user_tools import user_is_admin
from crits.disassembly.forms import UploadDisassemblyFileForm
from crits.disassembly.forms import NewDisassemblyTypeForm
from crits.disassembly.handlers import update_disassembly_description
from crits.disassembly.handlers import update_disassembly_tool_details
from crits.disassembly.handlers import update_disassembly_tool_name
from crits.disassembly.handlers import update_disassembly_type
from crits.disassembly.handlers import handle_disassembly_file
from crits.disassembly.handlers import delete_disassembly, get_disassembly_details
from crits.disassembly.handlers import generate_disassembly_jtable
from crits.disassembly.handlers import generate_disassembly_csv
from crits.disassembly.handlers import generate_disassembly_versions
from crits.disassembly.handlers import get_id_from_link_and_version
from crits.disassembly.handlers import add_new_disassembly_type
from crits.disassembly.disassembly import DisassemblyType

@user_passes_test(user_can_view_data)
def disassembly_listing(request, option=None):
    """
    Generate Disassembly Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_disassembly_csv(request)
    return generate_disassembly_jtable(request, option)

@user_passes_test(user_can_view_data)
def set_disassembly_description(request, _id):
    """
    Set the Disassembly description. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Disassembly.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        description = request.POST['description']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_disassembly_description(_id,
                                                               description,
                                                               analyst)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def set_disassembly_tool_details(request, _id):
    """
    Set the Disassembly tool details. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Disassembly.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        details = request.POST['details']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_disassembly_tool_details(_id,
                                                               details,
                                                               analyst)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def set_disassembly_tool_name(request, _id):
    """
    Set the Disassembly tool name. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Disassembly.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        name = request.POST['name']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_disassembly_tool_name(_id,
                                                               name,
                                                               analyst)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def set_disassembly_type(request, _id):
    """
    Set the Disassembly datatype. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Disassembly.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        data_type = request.POST['data_type']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_disassembly_type(_id,
                                                            data_type,
                                                            analyst)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def get_disassembly_versions(request, _id):
    """
    Get a list of versions for Disassembly. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Disassembly.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        return HttpResponse(json.dumps(generate_disassembly_versions(_id)),
                            mimetype="application/json")
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def disassembly_details(request, _id):
    """
    Generate Disassembly details page.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Disassembly.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    template = 'disassembly_details.html'
    analyst = request.user.username
    (new_template, args) = get_disassembly_details(_id, analyst)
    if new_template:
        template = new_template
    return render_to_response(template,
                              args,
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def details_by_link(request, link):
    """
    Generate Disassembly details page by link.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param link: The LinkId of the Disassembly.
    :type link: str
    :returns: :class:`django.http.HttpResponse`
    """

    version = request.GET.get('version', 1)
    return disassembly_details(request,
                               get_id_from_link_and_version(link, version))

@user_passes_test(user_can_view_data)
def upload_disassembly(request, link_id=None):
    """
    Upload new Disassembly to CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param link_id: The LinkId of Disassembly if this is a new version upload.
    :type link_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        form = UploadDisassemblyFileForm(request.user,
                                         request.POST,
                                         request.FILES)
        if 'filedata' not in request.FILES:
            jdump = json.dumps({'success': False,
                                'message': 'Need a file.'})
            return render_to_response('file_upload_response.html',
                                      {'response': jdump},
                                      RequestContext(request))

        filedata = request.FILES['filedata']
        data = filedata.read() # XXX: Should be using chunks here.
        filename = filedata.name
        if not filename:
            filename = md5(data).hexdigest()

        if form.is_valid():
            source = form.cleaned_data.get('source')
            user = request.user.username
            description = form.cleaned_data.get('description', '')
            tool_name = form.cleaned_data.get('tool_name', '')
            tool_version = form.cleaned_data.get('tool_version', '')
            tool_details = form.cleaned_data.get('tool_details', '')
            data_type = form.cleaned_data.get('data_type', None)
            copy_rels = request.POST.get('copy_relationships', False)
            bucket_list = form.cleaned_data.get('bucket_list')
            ticket = form.cleaned_data.get('ticket')
            method = 'Upload'
            status = handle_disassembly_file(data, source, user,
                                             description, filename, data_type,
                                             tool_name, tool_version,
                                             tool_details, link_id,
                                             method=method,
                                             copy_rels=copy_rels,
                                             bucket_list=bucket_list,
                                             ticket=ticket)
            if status['success']:
                jdump = json.dumps({
                    'message': 'Disassembly uploaded successfully! <a href="%s">View disassembly</a>'
                    % reverse('crits.disassembly.views.disassembly_details',
                              args=[status['id']]), 'success': True})
            else:
                jdump = json.dumps({'success': False,
                                    'message': status['message']})
        else:
            jdump = json.dumps({'success': False,
                                'form': form.as_table()})
        return render_to_response('file_upload_response.html',
                                  {'response': jdump},
                                  RequestContext(request))
    else:
        return render_to_response('error.html',
                                  {'error': "Expected POST."},
                                  RequestContext(request))

@user_passes_test(user_is_admin)
def remove_disassembly(request, _id):
    """
    Remove Disassembly from CRITs.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param _id: The ObjectId of the Disassembly to remove.
    :type _id: str
    :returns: :class:`django.http.HttpResponse`
    """

    result = delete_disassembly(_id, '%s' % request.user.username)
    if result:
        return HttpResponseRedirect(reverse('crits.disassembly.views.disassembly_listing'))
    else:
        return render_to_response('error.html',
                                  {'error': "Could not delete disassembly"})

@user_passes_test(user_can_view_data)
def new_disassembly_type(request):
    """
    Add a new Disassembly datatype to CRITs. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        form = NewDisassemblyTypeForm(request.POST)
        analyst = request.user.username
        if form.is_valid():
            result = add_new_disassembly_type(form.cleaned_data['data_type'],
                                           analyst)
            if result:
                message = {'message': '<div>Disassembly Type added successfully!</div>',
                           'success': True}
            else:
                message = {'message': '<div>Disassembly Type addition failed!</div>',
                           'success': False}
        else:
            message = {'form': form.as_table()}
        return HttpResponse(json.dumps(message),
                            mimetype="application/json")
    return render_to_response('error.html',
                              {'error':'Expected AJAX POST'})


@user_passes_test(user_can_view_data)
def get_disassembly_type_dropdown(request):
    """
    Generate Disassembly datetypes dropdown information. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        dt_types = get_item_names(DisassemblyType)
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
