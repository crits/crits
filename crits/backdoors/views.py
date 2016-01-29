import json

from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.backdoors.forms import AddBackdoorForm
from crits.backdoors.handlers import add_new_backdoor, get_backdoor_details
from crits.backdoors.handlers import backdoor_remove, set_backdoor_name
from crits.backdoors.handlers import update_backdoor_aliases
from crits.backdoors.handlers import set_backdoor_version
from crits.backdoors.handlers import generate_backdoor_csv
from crits.backdoors.handlers import generate_backdoor_jtable
from crits.core import form_consts
from crits.core.data_tools import json_handler
from crits.core.user_tools import user_can_view_data, is_admin


@user_passes_test(user_can_view_data)
def backdoors_listing(request,option=None):
    """
    Generate the Backdoor listing page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', 'csv', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_backdoor_csv(request)
    return generate_backdoor_jtable(request, option)

@user_passes_test(user_can_view_data)
def backdoor_detail(request, id_):
    """
    Generate the Backdoor details page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param id_: The Backdoor ObjectId to get details for.
    :type id_: str
    :returns: :class:`django.http.HttpResponse`
    """

    template = "backdoor_detail.html"
    user = request.user.username
    (new_template, args) = get_backdoor_details(id_, user)
    if new_template:
        template = new_template
    return render_to_response(template,
                              args,
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def add_backdoor(request):
    """
    Add a backdoor. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        data = request.POST
        form = AddBackdoorForm(request.user, data)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            name = cleaned_data['name']
            aliases = cleaned_data['aliases']
            description = cleaned_data['description']
            version = cleaned_data['version']
            source = cleaned_data['source']
            reference = cleaned_data['source_reference']
            method = cleaned_data['source_method']
            campaign = cleaned_data['campaign']
            confidence = cleaned_data['confidence']
            user = request.user.username
            bucket_list = cleaned_data.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
            ticket = cleaned_data.get(form_consts.Common.TICKET_VARIABLE_NAME)

            result = add_new_backdoor(name,
                                      version=version,
                                      aliases=aliases,
                                      description=description,
                                      source=source,
                                      source_method=method,
                                      source_reference=reference,
                                      campaign=campaign,
                                      confidence=confidence,
                                      user=user,
                                      bucket_list=bucket_list,
                                      ticket=ticket)
            return HttpResponse(json.dumps(result, default=json_handler),
                                content_type="application/json")
        return HttpResponse(json.dumps({'success': False,
                                        'form':form.as_table()}),
                            content_type="application/json")
    return render_to_response("error.html",
                              {'error': 'Expected AJAX/POST'},
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def remove_backdoor(request, id_):
    """
    Remove a Backdoor.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param id_: The ObjectId of the Backdoor to remove.
    :type id_: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST":
        if is_admin(request.user):
            backdoor_remove(id_, request.user.username)
            return HttpResponseRedirect(reverse('crits.backdoors.views.backdoors_listing'))
        error = 'You do not have permission to remove this item.'
        return render_to_response("error.html",
                                  {'error': error},
                                  RequestContext(request))
    return render_to_response('error.html',
                              {'error':'Expected AJAX/POST'},
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def edit_backdoor_name(request, id_):
    """
    Set backdoor name. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param id_: The ObjectId of the Backdoor.
    :type id_: str
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        user = request.user.username
        name = request.POST.get('name', None)
        if not name:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Not all info provided.'}),
                                content_type="application/json")
        result = set_backdoor_name(id_,
                                   name,
                                   user)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def edit_backdoor_aliases(request):
    """
    Update aliases for a Backdoor.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        aliases = request.POST.get('aliases', None)
        id_ = request.POST.get('oid', None)
        user = request.user.username
        result = update_backdoor_aliases(id_, aliases, user)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def edit_backdoor_version(request, id_):
    """
    Set backdoor version. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param id_: The ObjectId of the Backdoor.
    :type id_: str
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        user = request.user.username
        version = request.POST.get('version', None)
        if version == None:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Not all info provided.'}),
                                content_type="application/json")
        result = set_backdoor_version(id_, version, user)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))
