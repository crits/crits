import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.template.loader import render_to_string

from crits.core.class_mapper import class_from_id
from crits.core.user_tools import user_can_view_data, user_is_admin
from crits.services.core import ServiceAnalysisError
from crits.services.handlers import make_edit_config_form, make_run_config_form
from crits.services.handlers import update_config, do_edit_config
from crits.services.handlers import get_service_config
from crits.services.handlers import set_enabled, set_triage
from crits.services.service import CRITsService
import crits.services

logger = logging.getLogger(__name__)


DETAIL_VIEWS = {
                'Certificate': 'crits.certificates.views.certificate_details',
                'Sample': 'crits.samples.views.detail',
                'PCAP': 'crits.pcaps.views.pcap_details',
                'RawData': 'crits.raw_data.views.raw_data_details',
                'Event': 'crits.events.views.view_event',
                'Indicator': 'crits.indicators.views.indicator',
                'Domain': 'crits.domains.views.domain_detail',
                'IP': 'crits.ips.views.ip_detail',
               }


@user_passes_test(user_is_admin)
def list(request):
    """
    List all services.
    """

    all_services = CRITsService.objects().order_by('+name')
    return render_to_response('services_list.html', {'services': all_services},
                              RequestContext(request))


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
    return HttpResponse(json.dumps(result), mimetype="application/json")


@user_passes_test(user_is_admin)
def disable(request, name):
    """
    Disable a service.
    """

    result = set_enabled(name, False, request.user.username)
    return HttpResponse(json.dumps(result), mimetype="application/json")


@user_passes_test(user_is_admin)
def enable_triage(request, name):
    """
    Enable a service to run during triage.
    """

    result = set_triage(name, True, request.user.username)
    return HttpResponse(json.dumps(result), mimetype="application/json")


@user_passes_test(user_is_admin)
def disable_triage(request, name):
    """
    Disable a service from running during triage.
    """

    result = set_triage(name, False, request.user.username)
    return HttpResponse(json.dumps(result), mimetype="application/json")


@user_passes_test(user_is_admin)
def edit_config(request, name):
    """
    Edit a service's configuration.
    """

    analyst = request.user.username
    if request.method == "POST":
        results = do_edit_config(name, analyst, post_data=request.POST)
        if results['success'] == True:
            return redirect(reverse('crits.services.views.detail', args=[name]))
        else:
            return render_to_response('services_edit_config.html',
                                      {'form': results['form'],
                                       'service': results['service'],
                                       'config_error': results['config_error']},
                                      RequestContext(request))
    else:
        results = do_edit_config(name, analyst)
        if results['success'] == True:
            return render_to_response('services_edit_config.html',
                                      {'form': results['form'],
                                       'service': results['service']},
                                      RequestContext(request))
        else:
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

    service = CRITsService.objects(name=name,
                                   status__ne="unavailable").first()
    if not service:
        msg = 'Service "%s" is unavailable. Please review error logs.' % name
        response['error'] = msg
        return HttpResponse(json.dumps(response), mimetype="application/json")

    # Get the class that implements this service.
    service_class = crits.services.manager.get_service_class(name)

    # format_config returns a list of tuples
    config = service_class.format_config(service.config, printable=False)

    form_html = make_run_config_form(service_class,
                                     config,
                                     name,
                                     request,
                                     analyst=analyst,
                                     crits_type=crits_type,
                                     identifier=identifier)
    if not form_html:
        # this should only happen if there are no config options and the
        # service is rerunnable.
        response['redirect'] = reverse('crits.services.views.service_run',
                                        args=[name, crits_type, identifier])
    else:
        response['form'] = form_html

    return HttpResponse(json.dumps(response), mimetype="application/json")

@user_passes_test(user_can_view_data)
def refresh_services(request, crits_type, identifier):
    """
    Refresh the Analysis tab with the latest information.
    """

    response = {}

    obj = class_from_id(crits_type, identifier)
    if not obj:
        msg = 'Could not find object to refresh!'
        response['success'] = False
        response['html'] = msg
        return HttpResponse(json.dumps(response), mimetype="application/json")

    relationship = {'type': crits_type,
                    'value': identifier}

    subscription = {'type': crits_type,
                    'id': identifier}

    manager = crits.services.manager
    service_list = manager.get_supported_services(crits_type, True)

    response['success'] = True
    response['html'] = render_to_string("services_analysis_listing.html",
                                        {'relationship': relationship,
                                         'subscription': subscription,
                                         'item': obj,
                                         'crits_type': crits_type,
                                         'identifier': identifier,
                                         'service_list': service_list},
                                        RequestContext(request))

    return HttpResponse(json.dumps(response), mimetype="application/json")


@user_passes_test(user_can_view_data)
def service_run(request, name, crits_type, identifier):
    """
    Run a service.
    """

    response = {'success': False}
    if crits_type not in DETAIL_VIEWS:
        response['html'] = "Unknown CRITs type."
        return HttpResponse(json.dumps(response), mimetype="application/json")

    env = crits.services.environment
    username = str(request.user.username)

    # We can assume this is a DatabaseAnalysisEnvironment
    if name not in env.manager.enabled_services:
        response['html'] = "Service %s is unknown or not enabled." % name
        return HttpResponse(json.dumps(response), mimetype="application/json")

    service = CRITsService.objects(name=name,
                                   status__ne="unavailable").first()
    if not service:
        msg = 'Service "%s" is unavailable. Please review error logs.' % name
        response['error'] = msg
        return HttpResponse(json.dumps(response), mimetype="application/json")

    service_class = env.manager.get_service_class(name)
    config = service_class.format_config(service.config, printable=False)
    ServiceRunConfigForm = make_run_config_form(service_class,
                                                config,
                                                name,
                                                request,
                                                analyst=username,
                                                crits_type=crits_type,
                                                identifier=identifier,
                                                return_form=True)

    if request.method == "POST":
        #Populate the form with values from the POST request
        form = ServiceRunConfigForm(request.POST)
        if form.is_valid():
            # parse_config will remove the "force" option from cleaned_data
            config = service_class.parse_config(form.cleaned_data,
                                                exclude_private=True)
            force = form.cleaned_data.get("force")
        else:
            # TODO: return corrected form via AJAX
            response['html'] = "Invalid configuration, please try again :-("
            return HttpResponse(json.dumps(response), mimetype="application/json")
    else:
        # If not a POST, don't use any custom options.
        config = None
        force = False

    obj = class_from_id(crits_type, identifier)
    if not obj:
        response['html'] = 'Could not find object!'
        return HttpResponse(json.dumps(response), mimetype="application/json")

    try:
        env.run_service(name, obj, username, execute=settings.SERVICE_MODEL,
                        custom_config=config, force=force)
    except ServiceAnalysisError as e:
        logger.exception("Error when running service")
        response['html'] = "Error when running service: %s" % e
        return HttpResponse(json.dumps(response), mimetype="application/json")

    return refresh_services(request, crits_type, identifier)

@user_passes_test(user_is_admin)
def delete_task(request, crits_type, identifier, task_id):
    """
    Delete a service task.
    """

    # XXX: THIS USES DB_DEST FROM envrionment, which no longer exists
    #db_dest = crits.service_env.environment.dest
    #analyst = request.user.username

    #if crits_type in DETAIL_VIEWS:
    #    # Identifier is used since there's not currently an index on task_id
    #    db_dest.delete_analysis(crits_type, identifier, task_id, analyst)
    #    return refresh_services(request, crits_type, identifier)
    #else:
    #    error = 'Deleting tasks from type %s is not supported.' % crits_type
    #    return render_to_response('error.html', {'error': error},
    #                       RequestContext(request))
