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
import crits.service_env
from crits.services.core import ServiceAnalysisError
from crits.services.forms import (ImportServiceConfigForm,
        make_edit_config_form, make_run_config_form)
from crits.services.service import CRITsService

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


@user_passes_test(user_can_view_data)
def list(request):
    """
    List all services.
    """

    all_services = CRITsService.objects().order_by('+name')
    return render_to_response('services_list.html', {'services': all_services},
                              RequestContext(request))


@user_passes_test(user_can_view_data)
def detail(request, name):
    """
    List all details about a single service.
    """

    service = CRITsService.objects(name=name,
                                   status__ne="unavailable").first()

    if not service:
        error = 'Service "%s" is unavailable. Please review error logs.' % name
        return render_to_response('error.html', {'error': error},
                           RequestContext(request))
    # TODO: fix code so we don't have to do this
    service = service.to_dict()

    service_class = crits.service_env.manager.get_service_class(name)

    if user_is_admin(request.user):
        clean = False
        # Only show errors if the user is an admin.
        error = _get_config_error(service)
    else:
        # Clean all non-public values for a non-admin
        clean = True
        error = None

    # Replace the dictionary with a list (to preserve order the options
    # were defined in the Service class), and remove data from any which
    # are not editable)
    service['config_list'] = service_class.format_config(service['config'],
                                                         clean=clean)
    del service['config']
    return render_to_response('services_detail.html',
                              {'service': service, 'config_error': error},
                              RequestContext(request))


@user_passes_test(user_is_admin)
def enable(request, name):
    """
    Enable a service.
    """

    return _service_set_enabled(request, name, True)


@user_passes_test(user_is_admin)
def disable(request, name):
    """
    Disable a service.
    """

    return _service_set_enabled(request, name, False)


# No decorator since this is a private function
def _service_set_enabled(request, name, enabled=True):
    """
    Enable or disable a service.

    Returns the user back to the page they clicked on the link from. In case
    the user got here by manually typing the URL, go to the services list.
    """

    analyst = request.user.username
    crits.service_env.manager.set_enabled(name, enabled, analyst)
    if enabled:
        url = reverse('crits.services.views.disable', args=(name,))
    else:
        url = reverse('crits.services.views.enable', args=(name,))
    result = {'success': True,
              'url': url}
    return HttpResponse(json.dumps(result), mimetype="application/json")


@user_passes_test(user_is_admin)
def enable_triage(request, name):
    """
    Enable a service to run during triage.
    """

    return _service_set_triage_enabled(request, name, True)


@user_passes_test(user_is_admin)
def disable_triage(request, name):
    """
    Disable a service from running during triage.
    """

    return _service_set_triage_enabled(request, name, False)


# No decorator since this is a private function
def _service_set_triage_enabled(request, name, enabled=True):
    """
    Set whether or not a service runs during triage.

    Returns the user back to the page they clicked on the link from. In case
    the user got here by manually typing the URL, go to the services list.
    """

    analyst = request.user.username
    crits.service_env.manager.set_triage(name, enabled, analyst)
    if enabled:
        url = reverse('crits.services.views.disable_triage', args=(name,))
    else:
        url = reverse('crits.services.views.enable_triage', args=(name,))
    result = {'success': True,
              'url': url}
    return HttpResponse(json.dumps(result), mimetype="application/json")


@user_passes_test(user_is_admin)
def edit_config(request, name):
    """
    Edit a service's configuration.
    """

    analyst = request.user.username
    service = CRITsService.objects(name=name,
                                   status__ne="unavailable").first()
    if not service:
        error = 'Service "%s" is unavailable. Please review error logs.' % name
        return render_to_response('error.html', {'error': error},
                           RequestContext(request))
    # TODO: fix code so we don't have to do this
    service = service.to_dict()

    # Get the class that implements this service.
    service_class = crits.service_env.manager.get_service_class(name)

    # format_config returns a list of tuples
    old_config = service_class.format_config(service['config'],
                                             printable=False)

    logger.debug("old_config")
    logger.debug(str(old_config))

    ServiceEditConfigForm = make_edit_config_form(service_class)

    if request.method == "POST":
        #Populate the form with values from the POST request
        form = ServiceEditConfigForm(request.POST)
        if form.is_valid():
            logger.debug("Ingoing data:")
            logger.debug(str(form.cleaned_data))
            new_config = service_class.parse_config(form.cleaned_data)

            logger.info("Service %s configuration modified." % name)
            logger.debug(str(new_config))

            result = crits.service_env.manager.update_config(name, new_config,
                                                             analyst)

            if not result['success']:
                return render_to_response('error.html',
                                          {'error': result['message']},
                                          RequestContext(request))

            return redirect(reverse('crits.services.views.detail',
                                    args=[name]))
        else:
            # Return the form to the user to fix any errors.
            pass

    else:
        # Populate the form with the current values in the database.
        form = ServiceEditConfigForm(dict(old_config))

    error = _get_config_error(service)

    return render_to_response('services_edit_config.html',
                              {
                                'form': form,
                                'service': service,
                                'config_error': error,
                              },
                              RequestContext(request))


def _get_config_error(service):
    """
    Return a string describing the error in the service configuration.

    Returns None if there are no errors.
    """

    error = None
    name = service['name']
    config = service['config']
    if service['status'] == 'misconfigured':
        service_class = crits.service_env.manager.get_service_class(name)
        try:
            service_class.validate(config)
        except Exception as e:
            error = str(e)
    return error


@user_passes_test(user_is_admin)
def export_config(request, name):
    """
    Export a service's configuration.
    """

    # TODO: Present a form to the admin to select file format
    # Format is either ini or json
    s = CRITsService.objects(name=name).first()
    if s:
        try:
            data = json.dumps(s.config.to_dict())

        except (ValueError, TypeError) as e:
            error = 'Failed to export %s configuration, please check ' \
                    'error logs.' % name
            logger.error(error)
            logger.error(e)
            return render_to_response('error.html', {'error': error},
                                      RequestContext(request))

        response = HttpResponse(data, content_type='text/plain')
        response['Content-Length'] = len(data)
        fn = name + '.conf'
        response['Content-Disposition'] = 'attachment; filename="%s"' % fn
        return response

    else:
        error = 'Service "%s" does not exist!' % name
        render_to_response('error.html', {'error': error},
                           RequestContext(request))


@user_passes_test(user_is_admin)
def import_config(request, name):
    """
    Import a service's configuration.
    """

    if request.method == 'POST':
        analyst = request.user.username
        form = ImportServiceConfigForm(request.POST, request.FILES)
        if form.is_valid():
            data = ''
            for chunk in request.FILES['file'].chunks():
                data += chunk

            try:
                new_config = json.loads(data)

            except (ValueError, TypeError) as e:
                error = "Failed to import %s configuration, please check " \
                        "error logs." % name
                logger.error(error)
                logger.error(e)
                return render_to_response('error.html', {'error': error},
                                          RequestContext(request))

            current_config = CRITsService.objects(name=name).first().config

            # Check to ensure all keys in current config are in new config
            missing_keys = set(current_config.to_dict().keys()) - set(new_config.keys())
            if missing_keys:
                error = "Imported config is missing required fields: %s" \
                        % str(missing_keys)
                logger.error(error)
                return render_to_response('error.html',
                                          {'error': error},
                                          RequestContext(request))

            # Issue warnings when new keys are added
            added_keys = set(new_config.keys()) - set(current_config.to_dict().keys())
            if added_keys:
                warning = "Imported config contains new fields: %s" \
                          % str(added_keys)
                logger.warning(warning)

            result = crits.service_env.manager.update_config(name, new_config,
                                                             analyst)

            if not result['success']:
                return render_to_response('error.html',
                                          {'error': result['message']},
                                          RequestContext(request))

            return redirect(reverse('crits.services.views.detail',
                                    args=[name]))

        else:
            return render_to_response('error.html', {'error': form.errors},
                                      RequestContext(request))

    else:
        form = ImportServiceConfigForm()

    return render_to_response('services_import_config.html',
                              {'form': form, 'name': name},
                              RequestContext(request))


@user_passes_test(user_is_admin)
def reset_config(request, name):
    """
    Reset a service's configuration.

    This uses the values from the service class's default_config variable.
    """

    s = CRITsService.objects(name=name).first()
    if not s:
        error = 'Service "%s" does not exist or is not configured properly.' \
                ' Please Review error logs.' % name
        return render_to_response('error.html', {'error': error},
                           RequestContext(request))

    result = crits.service_env.manager.reset_config(name, request.user.username)

    if not result['success']:
        return render_to_response('error.html',
                                  {'error': result['message']},
                                  RequestContext(request))

    return redirect(reverse('crits.services.views.detail',
                            args=[name]))


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
    service_class = crits.service_env.manager.get_service_class(name)

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

    manager = crits.service_env.manager
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

    env = crits.service_env.environment
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

    db_dest = crits.service_env.environment.dest
    analyst = request.user.username

    if crits_type in DETAIL_VIEWS:
        # Identifier is used since there's not currently an index on task_id
        db_dest.delete_analysis(crits_type, identifier, task_id, analyst)
        return refresh_services(request, crits_type, identifier)
    else:
        error = 'Deleting tasks from type %s is not supported.' % crits_type
        return render_to_response('error.html', {'error': error},
                           RequestContext(request))
