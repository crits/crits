import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string

from crits.core.class_mapper import class_from_type
from crits.core.user_tools import user_can_view_data, user_is_admin, user_sources
from crits.services.analysis_result import AnalysisResult
from crits.services.handlers import do_edit_config, generate_analysis_results_csv
from crits.services.handlers import generate_analysis_results_jtable
from crits.services.handlers import get_service_config, set_enabled, set_triage
from crits.services.handlers import run_service, get_supported_services
from crits.services.handlers import delete_analysis
from crits.services.service import CRITsService
import crits.services

logger = logging.getLogger(__name__)


@user_passes_test(user_can_view_data)
def analysis_results_listing(request,option=None):
    """
    Generate Analysis Results Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_analysis_results_csv(request)
    return generate_analysis_results_jtable(request, option)

@user_passes_test(user_is_admin)
def list(request):
    """
    List all services.
    """

    all_services = CRITsService.objects().order_by('+name')
    return render_to_response('services_list.html', {'services': all_services},
                              RequestContext(request))


@user_passes_test(user_can_view_data)
def analysis_result(request, analysis_id):
    """
    Get the TLO type and object_id and redirect to the details page for that
    TLO.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param analysis_id: The ObjectId of the AnalysisResult
    :type analysis_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    ar = AnalysisResult.objects(id=analysis_id).first()
    if ar:
        return HttpResponseRedirect(reverse('crits.core.views.details',
                                            args=(ar.object_type,ar.object_id)))
    else:
        return render_to_response('error.html',
                                  {'error': "No TLO found to redirect to."})


@user_passes_test(user_is_admin)
def detail(request, name):
    """
    List all details about a single service.
    """

    results = get_service_config(name)
    if results['success']:
        return render_to_response('services_detail.html',
                                  {'service': results['service'],
                                   'config': results['config'],
                                   'config_error': results['config_error']},
                                  RequestContext(request))
    else:
        return render_to_response('error.html', {'error': results['error']},
                                  RequestContext(request))


@user_passes_test(user_is_admin)
def enable(request, name):
    """
    Enable a service.
    """

    result = set_enabled(name, True, request.user.username)
    return HttpResponse(json.dumps(result), content_type="application/json")


@user_passes_test(user_is_admin)
def disable(request, name):
    """
    Disable a service.
    """

    result = set_enabled(name, False, request.user.username)
    return HttpResponse(json.dumps(result), content_type="application/json")


@user_passes_test(user_is_admin)
def enable_triage(request, name):
    """
    Enable a service to run during triage.
    """

    result = set_triage(name, True, request.user.username)
    return HttpResponse(json.dumps(result), content_type="application/json")


@user_passes_test(user_is_admin)
def disable_triage(request, name):
    """
    Disable a service from running during triage.
    """

    result = set_triage(name, False, request.user.username)
    return HttpResponse(json.dumps(result), content_type="application/json")


@user_passes_test(user_is_admin)
def edit_config(request, name):
    """
    Edit a service's configuration.
    """

    analyst = request.user.username
    if request.method == "POST" and request.is_ajax():
        results = do_edit_config(name, analyst, post_data=request.POST)
        if 'service' in results:
            del results['service']
        return HttpResponse(json.dumps(results), content_type="application/json")
    elif request.method == "POST" and not request.is_ajax():
        error = results['config_error']
        return render_to_response('error.html',
                                  {'error': "Expected AJAX POST."},
                                  RequestContext(request))
    else:
        results = do_edit_config(name, analyst)
        if results['success'] == True:
            return render_to_response('services_edit_config.html',
                                      {'form': results['form'],
                                       'service': results['service']},
                                      RequestContext(request))
        else:
            error = results['config_error']
            return render_to_response('error.html', {'error': error},
                                      RequestContext(request))


@user_passes_test(user_can_view_data)
def get_form(request, name, crits_type, identifier):
    """
    Get a configuration form for a service.
    """

    response = {}
    response['name'] = name
    analyst = request.user.username

    service = CRITsService.objects(name=name, status__ne="unavailable").first()
    if not service:
        msg = 'Service "%s" is unavailable. Please review error logs.' % name
        response['error'] = msg
        return HttpResponse(json.dumps(response), content_type="application/json")

    # Get the class that implements this service.
    service_class = crits.services.manager.get_service_class(name)

    config = service.config.to_dict()

    form_html = service_class.generate_runtime_form(analyst,
                                                    config,
                                                    crits_type,
                                                    identifier)
    if not form_html:
        return service_run(request, name, crits_type, identifier)
    else:
        response['form'] = form_html

    return HttpResponse(json.dumps(response), content_type="application/json")


@user_passes_test(user_can_view_data)
def refresh_services(request, crits_type, identifier):
    """
    Refresh the Analysis tab with the latest information.
    """

    response = {}

    # Verify user can see results.
    sources = user_sources(request.user.username)
    klass = class_from_type(crits_type)
    if not klass:
        msg = 'Could not find object to refresh!'
        response['success'] = False
        response['html'] = msg
        return HttpResponse(json.dumps(response), content_type="application/json")
    if hasattr(klass, 'source'):
        obj = klass.objects(id=identifier,source__name__in=sources).first()
    else:
        obj = klass.objects(id=identifier).first()
    if not obj:
        msg = 'Could not find object to refresh!'
        response['success'] = False
        response['html'] = msg
        return HttpResponse(json.dumps(response), content_type="application/json")

    # Get analysis results.
    results = AnalysisResult.objects(object_type=crits_type,
                                     object_id=identifier)

    relationship = {'type': crits_type,
                    'value': identifier}

    subscription = {'type': crits_type,
                    'id': identifier}

    service_list = get_supported_services(crits_type)

    response['success'] = True
    response['html'] = render_to_string("services_analysis_listing.html",
                                        {'relationship': relationship,
                                         'subscription': subscription,
                                         'service_results': results,
                                         'crits_type': crits_type,
                                         'identifier': identifier,
                                         'service_list': service_list},
                                        RequestContext(request))

    return HttpResponse(json.dumps(response), content_type="application/json")


@user_passes_test(user_can_view_data)
def service_run(request, name, crits_type, identifier):
    """
    Run a service.
    """

    username = str(request.user.username)

    if request.method == 'POST':
        custom_config = request.POST
    elif request.method == "GET":
        # Run with no config...
        custom_config = {}

    result = run_service(name,
                         crits_type,
                         identifier,
                         username,
                         execute=settings.SERVICE_MODEL,
                         custom_config=custom_config)
    if result['success'] == True:
        return refresh_services(request, crits_type, identifier)
    else:
        return HttpResponse(json.dumps(result), content_type="application/json")


@user_passes_test(user_is_admin)
def delete_task(request, crits_type, identifier, task_id):
    """
    Delete a service task.
    """

    analyst = request.user.username

    # Identifier is used since there's not currently an index on task_id
    delete_analysis(task_id, analyst)
    return refresh_services(request, crits_type, identifier)
