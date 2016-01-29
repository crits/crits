import json

from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.template import RequestContext

from crits.core.handlers import get_item_names
from crits.core.user_tools import user_can_view_data
from crits.core.user_tools import user_is_admin
from crits.signatures.forms import UploadSignatureForm
from crits.signatures.forms import NewSignatureTypeForm
from crits.signatures.forms import NewSignatureDependencyForm
from crits.signatures.handlers import update_signature_type, update_min_version, update_max_version, update_dependency
from crits.signatures.handlers import handle_signature_file
from crits.signatures.handlers import get_dependency_autocomplete
from crits.signatures.handlers import delete_signature, get_signature_details, delete_signature_dependency
from crits.signatures.handlers import generate_signature_jtable
from crits.signatures.handlers import generate_signature_csv
from crits.signatures.handlers import generate_signature_versions
from crits.signatures.handlers import get_id_from_link_and_version
from crits.signatures.handlers import add_new_signature_type
from crits.signatures.handlers import add_new_signature_dependency
from crits.signatures.signature import SignatureType
from crits.signatures.signature import SignatureDependency

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
def set_signature_type(request, id_):
    """
    Set the Signature datatype. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param id_: The ObjectId of the Signature.
    :type id_: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        data_type = request.POST['data_type']
        type_ = request.POST['type']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_signature_type(type_,
                                                             id_,
                                                            data_type,
                                                            analyst)),
                            content_type="application/json")
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
                            content_type="application/json")
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

    return render(request, template, args)

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
            analyst = request.user.username
            data = request.POST.get('data', None)
            source = form.cleaned_data.get('source')
            user = request.user.username
            description = form.cleaned_data.get('description', '')
            title = form.cleaned_data.get('title', None)
            data_type = form.cleaned_data.get('data_type', None)
            data_type_min_version = form.cleaned_data.get('data_type_min_version', None)
            data_type_max_version = form.cleaned_data.get('data_type_max_version', None)

            ''' Parse out dependencies and add any new ones '''
            depend_string = form.cleaned_data.get('data_type_dependency', None)
            new_list = depend_string.split(',')
            data_type_dependency = []

            for dtd in new_list:
                dtd = dtd.strip()
                dtd = str(dtd)
                if dtd:
                    data_type_dependency.append(dtd)
                    add_new_signature_dependency(dtd,analyst)

            copy_rels = request.POST.get('copy_relationships', False)
            link_id = link_id
            bucket_list = form.cleaned_data.get('bucket_list')
            ticket = form.cleaned_data.get('ticket')
            method = form.cleaned_data.get('method', '') or 'Upload'
            reference = form.cleaned_data.get('reference', '')
            status = handle_signature_file(data, source, user,
                                          description, title, data_type,
                                          data_type_min_version,
                                          data_type_max_version,
                                          data_type_dependency, link_id,
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
                return HttpResponse(jdump, content_type="application/json")

            else:
                jdump = json.dumps({'success': False,
                                    'message': status['message']})
                return HttpResponse(jdump, content_type="application/json")

        else:
            jdump = json.dumps({'success': False,
                                'form': form.as_table()})
            return HttpResponse(jdump, content_type="application/json")

    else:
        return render_to_response('error.html',
                                  {'error': "Expected POST."},
                                  RequestContext(request))


@user_passes_test(user_can_view_data)
def update_data_type_dependency(request):
    """
    Update the dependency list in the signature.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        type_ = request.POST['type']
        id_ = request.POST['id']
        data_deps = request.POST['data_type_dependency']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_dependency(type_,
                                                          id_,
                                                          data_deps,
                                                          analyst)),
                            content_type="application/json")
    else:
        return render_to_response("error.html",
                                  {"error" : 'Expected AJAX POST.'},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def update_data_type_min_version(request):
    """
    Update the min version number in the signature.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        type_ = request.POST['type']
        id_ = request.POST['id']
        data_type_min_version = request.POST['data_type_min_version']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_min_version(type_,
                                                          id_,
                                                          data_type_min_version,
                                                          analyst)),
                            content_type="application/json")
    else:
        return render_to_response("error.html",
                                  {"error" : 'Expected AJAX POST.'},
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def update_data_type_max_version(request):
    """
    Update the max version number in the signature.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        type_ = request.POST['type']
        id_ = request.POST['id']
        data_type_max_version = request.POST['data_type_max_version']
        analyst = request.user.username
        return HttpResponse(json.dumps(update_max_version(type_,
                                                          id_,
                                                          data_type_max_version,
                                                          analyst)),
                            content_type="application/json")
    else:
        return render_to_response("error.html",
                                  {"error" : 'Expected AJAX POST.'},
                                  RequestContext(request))


@user_passes_test(user_is_admin)
def remove_signature_dependency(request):
    """
    Remove Signature Dependency from CRITs
    :param request: Django request object (Required)
    :param _id: THe ObjectId of the Signature Dependency to remove.

    :return: :class: 'django.http.HttpResponse'
    """


    if request.method == 'POST' and request.is_ajax():
        type_ = request.POST.get('coll', None)
        oid = request.POST.get('oid', None)

        if not oid or not type_:
            result = {'success': False}
        else:
            result = delete_signature_dependency(oid, '%s' % request.user.username)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
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
def new_signature_dependency(request):
    """
    Add a new Signature dependency to CRITs. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """


    if request.method == 'POST' and request.is_ajax():
        form = NewSignatureDependencyForm(request.POST)
        analyst = request.user.username
        if form.is_valid():

            result = add_new_signature_dependency(form.cleaned_data['data_type_dependency'],
                                           analyst)
            if result:
                message = {'message': '<div>Signature Dependency added successfully!</div>',
                           'success': True}
            else:
                message = {'message': '<div>Signature Dependency addition failed!</div>',
                           'success': False}
        else:
            message = {'form': form.as_table()}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")
    else:
        return render_to_response('error.html',
                              {'error':'Expected AJAX POST'})


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
                            content_type="application/json")
    return render_to_response('error.html',
                              {'error':'Expected AJAX POST'})



@user_passes_test(user_can_view_data)
def get_signature_dependency_dropdown(request):
    """
    Generate Signature dependency dropdown information. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        dt_deps = get_item_names(SignatureDependency)
        dt_final = []
        for dt in dt_deps:
            dt_final.append(dt.name)
            result = {'data': dt_final}
            return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {'error': error},
                                  RequestContext(request))


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
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {'error': error},
                                  RequestContext(request))


@user_passes_test(user_can_view_data)
def dependency_autocomplete(request):
    """
    Get a list of autocomplete options
    :param request: Request with JSON containing the initial characters
    :return: HttpResponse with JSON with list of options
    """

    if request.method == "POST" and request.is_ajax():
        term = request.POST.get('term', None)
        if term:
            return get_dependency_autocomplete(term)
    return HttpResponse({})

