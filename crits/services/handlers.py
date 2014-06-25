import ast
import datetime
import logging

from mongoengine.base import ValidationError

from django.core.urlresolvers import reverse

from crits.core.class_mapper import class_from_type, class_from_id
from crits.core.crits_mongoengine import EmbeddedAnalysisResult, AnalysisConfig
from crits.core.user_tools import user_sources
from crits.services.core import ServiceConfigError
from crits.services.service import CRITsService
import crits.services

logger = logging.getLogger(__name__)

def run_triage(obj, user):
    """
    Run all services marked as triage against this top-level object.

    :param obj: The CRITs top-level object class.
    :type obj: Class which inherits from
               :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param user: The user requesting the services to be run.
    :type user: str
    """

    #TODO: make this work
    #env = crits.service_env.environment
    #for service_name in env.manager.triage_services:
    #    try:
    #        env.run_service(service_name,
    #                        obj,
    #                        user,
    #                        execute=settings.SERVICE_MODEL)
    #    except:
    #        pass
    #return
    return


def add_result(object_type, object_id, analysis_id, result, type_, subtype,
               analyst):
    """
    Add a result to an analysis task.

    :param object_type: The top-level object type.
    :type object_type: str
    :param object_id: The ObjectId to search for.
    :type object_id: str
    :param analysis_id: The ID of the task to update.
    :type analysis_id: str
    :param result: The result to append.
    :type result: str
    :param type_: The result type.
    :type type_: str
    :param subtype: The result subtype.
    :type subtype: str
    :param analyst: The user updating the results.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    res = {'success': False}
    if not object_type or not object_id or not analysis_id:
        res['message'] = "Must supply object id/type and analysis id."
        return res
    klass = class_from_type(object_type)
    sources = user_sources(analyst)
    obj = klass.objects(id=object_id, source__name__in=sources).first()
    if not obj:
        res['message'] = "Could not find object to add results to."
        return res
    found = False
    c = 0
    for a in obj.analysis:
        if str(a.analysis_id) == analysis_id:
            found = True
            break
        c += 1
    if not found:
        res['message'] = "Could not find an analysis task to update."
        return res
    if result and type_ and subtype:
        final = {}
        final['subtype'] = subtype
        final['result'] = result
        tmp = ast.literal_eval(type_)
        for k in tmp:
            final[k] = tmp[k]
        klass.objects(id=object_id,
                        analysis__id=analysis_id).update_one(push__analysis__S__results=final)
    else:
        res['message'] = "Need a result, type, and subtype to add a result."
        return res
    res['success'] = True
    return res


def add_log(object_type, object_id, analysis_id, log_message, level, analyst):
    """
    Add a log entry to an analysis task.

    :param object_type: The top-level object type.
    :type object_type: str
    :param object_id: The ObjectId to search for.
    :type object_id: str
    :param analysis_id: The ID of the task to update.
    :type analysis_id: str
    :param log_message: The log entry to append.
    :type log_message: dict
    :param level: The log level.
    :type level: str
    :param analyst: The user updating the log.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    results = {'success': False}
    if not object_type or not object_id or not analysis_id:
        results['message'] = "Must supply object id/type and analysis id."
        return results
    klass = class_from_type(object_type)
    sources = user_sources(analyst)
    obj = klass.objects(id=object_id, source__name__in=sources).first()
    if not obj:
        results['message'] = "Could not find object to add log to."
        return results
    found = False
    c = 0
    for a in obj.analysis:
        if str(a.analysis_id) == analysis_id:
            found = True
            break
        c += 1
    if not found:
        results['message'] = "Could not find an analysis task to update."
        return results
    le = EmbeddedAnalysisResult.EmbeddedAnalysisResultLog()
    le.message = log_message
    le.level = level
    le.datetime = str(datetime.datetime.now())
    klass.objects(id=object_id,
                  analysis__id=analysis_id).update_one(push__analysis__S__log=le)
    results['success'] = True
    return results


def finish_task(object_type, object_id, analysis_id, status, analyst):
    """
    Finish a task by setting its status to "completed" and setting the finish
    date.

    :param object_type: The top-level object type.
    :type object_type: str
    :param object_id: The ObjectId to search for.
    :type object_id: str
    :param analysis_id: The ID of the task to update.
    :type analysis_id: str
    :param status: The status of the task.
    :type status: str ("error", "completed")
    :param analyst: The user updating the log.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    results = {'success': False}
    if not status:
        status = "completed"
    if status not in ('error', 'completed'):
        status = "completed"
    if not object_type or not object_id or not analysis_id:
        results['message'] = "Must supply object id/type and analysis id."
        return results
    klass = class_from_type(object_type)
    sources = user_sources(analyst)
    obj = klass.objects(id=object_id, source__name__in=sources).first()
    if not obj:
        results['message'] = "Could not find object to add log to."
        return results
    date = str(datetime.datetime.now())
    klass.objects(id=object_id,
                  analysis__id=analysis_id).update_one(set__analysis__S__status=status,
                                                       set__analysis__S__finish_date=date)
    results['success'] = True
    return results


def update_config(service_name, config, analyst):
    """
    Update the configuration for a service.
    """

    service = CRITsService.objects(name=service_name).first()
    service.config = AnalysisConfig(**config)
    try:
        #TODO: get/validate the config from service author to set status
        #update_status(service_name)
        service.save(username=analyst)
        return {'success': True}
    except ValidationError, e:
        return {'success': False,
                'message': e}

def get_service_config(name):
    status = {'success': False}
    service = CRITsService.objects(name=name, status__ne="unavailable").first()
    if not service:
        status['error'] = 'Service "%s" is unavailable. Please review error logs.' % name
        return status

    config = service.config.to_dict()
    service_class = crits.services.manager.get_service_class(name)
    if hasattr(service_class, 'get_config_details'):
        config = service_class.get_config_details(config)

    status['config'] = config
    status['config_error'] = _get_config_error(service)

    # TODO: fix code so we don't have to do this
    status['service'] = service.to_dict()

    status['success'] = True
    return status


def _get_config_error(service):
    """
    Return a string describing the error in the service configuration.

    Returns None if there are no errors.
    """

    error = None
    name = service['name']
    config = service['config']
    if service['status'] == 'misconfigured':
        service_class = crits.services.manager.get_service_class(name)
        try:
            service_class.parse_config(config.to_dict())
        except Exception as e:
            error = str(e)
    return error


def do_edit_config(name, analyst, post_data=None):
    status = {'success': False}
    service = CRITsService.objects(name=name, status__ne="unavailable").first()
    if not service:
        status['config_error'] = 'Service "%s" is unavailable. Please review error logs.' % name
        return status

    # Get the class that implements this service.
    service_class = crits.services.manager.get_service_class(name)

    # This isn't a form object. It's the HTML.
    status['form'] = make_edit_config_form(service_class, service)
    status['service'] = service

    if post_data:
        ServiceEditConfigForm = make_edit_config_form(service_class,
                                                      service,
                                                      return_form=True)
        #Populate the form with values from the POST request
        form = ServiceEditConfigForm(post_data)
        if form.is_valid():
            try:
                new_config = service_class.parse_config(form.cleaned_data)
            except ServiceConfigError as e:
                #service.status = 'misconfigured'
                #service.save()
                status['config_error'] = str(e)
                return status

            result = update_config(name, new_config, analyst)
            if not result['success']:
                return status

            service.status = 'available'
            service.save()
        else:
            status['config_error'] = form.errors
            return status

    status['success'] = True
    return status


def get_config(service_name):
    """
    Get the configuration for a service.
    """

    service = CRITsService.objects(name=service_name).first()
    return service.config

def set_enabled(service_name, enabled=True, analyst=None):
    """
    Enable/disable a service in CRITs.
    """

    if enabled:
        logger.info("Enabling: %s" % service_name)
    else:
        logger.info("Disabling: %s" % service_name)
    service = CRITsService.objects(name=service_name).first()
    service.enabled = enabled

    try:
        service.save(username=analyst)
        if enabled:
            url = reverse('crits.services.views.disable', args=(service_name,))
        else:
            url = reverse('crits.services.views.enable', args=(service_name,))
        return {'success': True, 'url': url}
    except ValidationError, e:
        return {'success': False, 'message': e}

def set_triage(service_name, enabled=True, analyst=None):
    """
    Enable/disable a service for running on triage (upload).
    """

    if enabled:
        logger.info("Enabling triage: %s" % service_name)
    else:
        logger.info("Disabling triage: %s" % service_name)
    service = CRITsService.objects(name=service_name).first()
    service.run_on_triage = enabled
    try:
        service.save(username=analyst)
        if enabled:
            url = reverse('crits.services.views.disable_triage',
                          args=(service_name,))
        else:
            url = reverse('crits.services.views.enable_triage',
                          args=(service_name,))
        return {'success': True, 'url': url}
    except ValidationError, e:
        return {'success': False,
                'message': e}

def enabled_services(status=True):
    """
    Return names of services which are enabled.
    """

    if status:
        services = CRITsService.objects(enabled=True,
                                        status="Available")
    else:
        services = CRITsService.objects(enabled=True)
    return [s.name for s in services]

def get_supported_services(crits_type):
    """
    Get the supported services for a type.
    """

    services = CRITsService.objects(enabled=True)
    for s in services:
        if s.supported_types == 'all' or crits_type in s.supported_types:
            yield s.name

def triage_services(status=True):
    """
    Return names of services set to run on triage.
    """

    if status:
        services = CRITsService.objects(run_on_triage=True,
                                        status="Available")
    else:
        services = CRITsService.objects(run_on_triage=True)
    return [s.name for s in services]

#TODO: rename?
def finish_task_(task):
    """
    Finish a task.
    """

    logger.debug("Finishing task %s" % task)
    update_analysis_results(task)

    obj = class_from_type(task.obj._meta['crits_type'])
    sample = obj.objects(id=task.obj.id).first()

    if task.files:
        logger.debug("Adding samples")
        for f in task.files:
            logger.debug("Adding %s" % f['filename'])
            #TODO: add in backdoor?, user
            from crits.samples.handlers import handle_file
            handle_file(f['filename'], f['data'], sample.source,
                        parent_md5=task.obj.id,
                        campaign=sample.campaign,
                        method=task.service.name,
                        relationship=f['relationship'],
                        user=task.username,
                        )
    else:
        logger.debug("No samples to add.")

    if task.certificates:
        logger.debug("Adding certificates")

        for f in task.certificates:
            logger.debug("Adding %s" % f['filename'])
            from crits.certificates.handlers import handle_cert_file
            # XXX: Add campaign from source?
            handle_cert_file(f['filename'], f['data'], sample.source,
                        parent_md5=task.obj.id,
                        parent_type=task.obj._meta['crits_type'],
                        method=task.service.name,
                        relationship=f['relationship'],
                        user=task.username,
                        )
    else:
        logger.debug("No certificates to add.")

    if task.pcaps:
        logger.debug("Adding PCAPs")

        for f in task.pcaps:
            logger.debug("Adding %s" % f['filename'])
            from crits.pcaps.handlers import handle_pcap_file
            # XXX: Add campaign from source?
            handle_pcap_file(f['filename'], f['data'], sample.source,
                        parent_md5=task.obj.identifier,
                        parent_type=task.obj._meta['crits_type'],
                        method=task.service.name,
                        relationship=f['relationship'],
                        user=task.username,
                        )
    else:
        logger.debug("No PCAPs to add.")

def delete_analysis(crits_type, identifier, task_id, analyst):
    """
    Delete analysis results.
    """

    obj = class_from_id(crits_type, identifier)
    if obj:
        c = 0
        for a in obj.analysis:
            if str(a.analysis_id) == task_id:
                del obj.analysis[c]
            c += 1
        obj.save(username=analyst)

def insert_analysis_results(task):
    """
    Insert analysis results for this task.
    """

    obj_class = class_from_type(task.obj._meta['crits_type'])

    ear = EmbeddedAnalysisResult()
    tdict = task.to_dict()
    tdict['analysis_type'] = tdict['type']
    tdict['analysis_id'] = tdict['id']
    del tdict['type']
    del tdict['id']
    ear.merge(arg_dict=tdict)
    ear.config = AnalysisConfig(**tdict['config'])
    obj_class.objects(id=task.obj.id).update_one(push__analysis=ear)

def update_analysis_results(task):
    """
    Update analysis results for this task.
    """

    # If the task does not currently exist for the given sample in the
    # database, add it.

    obj_class = class_from_type(task.obj._meta['crits_type'])

    obj = obj_class.objects(id=task.obj.id).first()
    obj_id = obj.id
    found = False
    c = 0
    for a in obj.analysis:
        if str(a.analysis_id) == task.task_id:
            found = True
            break
        c += 1

    if not found:
        logger.warning("Tried to update a task that didn't exist.")
        insert_analysis_results(task)
    else:
        # Otherwise, update it.
        ear = EmbeddedAnalysisResult()
        tdict = task.to_dict()
        tdict['analysis_type'] = tdict['type']
        tdict['analysis_id'] = tdict['id']
        del tdict['type']
        del tdict['id']
        ear.merge(arg_dict=tdict)
        ear.config = AnalysisConfig(**tdict['config'])
        obj_class.objects(id=obj_id,
                            analysis__id=task.task_id).update_one(set__analysis__S=ear)

def make_edit_config_form(service_class, service, return_form=False):
    """
    Return a Django Form for editing a service's config.

    This should be used when the administrator is editing a service
    configuration.
    """

    if hasattr(service_class, "generate_config_form"):
        (form, html) = service_class.generate_config_form(service)
        if return_form:
            return form
        return html
    return None

def make_run_config_form(service_class, config, name, request,
                         analyst=None, crits_type=None, identifier=None,
                         return_form=False):
    """
    Return a Django form used when running a service.

    If the service has a "generate_runtime_form()" method, use it. Otherwise
    generate a generic form using the config options.

    The "generate_runtime_form()" function must allow for passing in an analyst,
    name, crits_type, and identifier, even if it doesn't plan on using all of
    them.

    This is the same as make_edit_config_form, but adds a BooleanField
    (checkbox) for whether to "Force" the service to run.

    :param service_class: The service class.
    :type service_class: :class:`crits.services.core.Service`
    :param config: Configuration options for the service.
    :type config: dict
    :param name: Name of the form to use.
    :type name: str
    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :param analyst: The user requesting the form.
    :type analyst: str
    :param crits_type: The top-level object type.
    :type crits_type: str
    :param identifier: ObjectId of the top-level object.
    :type identifier: str
    :param return_form: Return a Django form object instead of HTML.
    :type return_form: boolean
    """

    if hasattr(service_class, "generate_runtime_form"):
        (form, html) = service_class.generate_runtime_form(analyst,
                                                           name,
                                                           config,
                                                           crits_type,
                                                           identifier)
        if return_form:
            return form
        return html
    return None
