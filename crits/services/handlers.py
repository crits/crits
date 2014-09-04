import ast
import datetime
import logging


from multiprocessing import Pool, Process
from multiprocessing.pool import ThreadPool
from threading import Thread

from mongoengine.base import ValidationError

from django.core.urlresolvers import reverse
from django.conf import settings

import crits.services

from crits.core.class_mapper import class_from_type, class_from_id
from crits.core.crits_mongoengine import EmbeddedAnalysisResult, AnalysisConfig
from crits.core.user_tools import user_sources
from crits.services.core import ServiceConfigError, AnalysisTask
from crits.services.service import CRITsService

logger = logging.getLogger(__name__)


def service_work_handler(service_instance, final_config):
    """
    Handles a unit of work for a service by calling the service's "execute"
    method. This function is generally called by processes/threads. Also
    this function is needed because it is picklable and passing in the
    service_instance.execute method is not picklable because it is an
    instance method.

    :param service_instance: The service instance that the work will be performed in
    :type service_instance: crits.services.core.Service
    :param service_instance: The service's configuration settings
    :type service_instance: dict
    """

    service_instance.execute(final_config)

def run_service(name, crits_type, identifier, analyst, obj=None,
                execute='local', custom_config={}):
    """
    Run a service.

    :param name: The name of the service to run.
    :type name: str
    :param crits_type: The type of the object.
    :type name: str
    :param identifier: The identifier of the object.
    :type name: str
    :param obj: The CRITs object, if given this overrides crits_type and identifier.
    :type obj: CRITs object.
    :param analyst: The user updating the results.
    :type analyst: str
    :param execute: The execution type.
    :type execute: str
    :param custom_config: Use a custom configuration for this run.
    :type custom_config: dict
    """

    result = {'success': False}
    if crits_type not in settings.CRITS_TYPES:
        result['html'] = "Unknown CRITs type."
        return result

    if name not in enabled_services():
        result['html'] = "Service %s is unknown or not enabled." % name
        return result

    service_class = crits.services.manager.get_service_class(name)
    if not service_class:
        result['html'] = "Unable to get service class."
        return result

    if not obj:
        obj = class_from_id(crits_type, identifier)
        if not obj:
            result['html'] = 'Could not find object.'
            return result

    service = CRITsService.objects(name=name).first()
    if not service:
        result['html'] = "Unable to find service in database."
        return result

    # See if the object is a supported type for the service.
    if not service_class.supported_for_type(crits_type):
        result['html'] = "Service not supported for type '%s'" % crits_type
        return result

    # Give the service a chance to check for required fields.
    try:
        service_class.valid_for(obj)
    except ServiceConfigError as e:
        result['html'] = str(e)
        return result

    # Get the config from the database and validate the submitted options
    # exist.
    db_config = service.config.to_dict()
    try:
        service_class.validate_runtime(custom_config, db_config)
    except ServiceConfigError as e:
        result['html'] = str(e)
        return result

    final_config = db_config
    # Merge the submitted config with the one from the database.
    # This is because not all config options may be submitted.
    final_config.update(custom_config)

    form = service_class.bind_runtime_form(analyst, final_config)
    if form:
        if not form.is_valid():
            # TODO: return corrected form via AJAX
            result['html'] = str(form.errors)
            return result

        # If the form is valid, create the config using the cleaned data.
        final_config = db_config
        final_config.update(form.cleaned_data)

    logger.info("Running %s on %s, execute=%s" % (name, obj.id, execute))
    service_instance = service_class(notify=update_analysis_results,
                                     complete=finish_task)

    # Give the service a chance to modify the config that gets saved to the DB.
    saved_config = dict(final_config)
    service_class.save_runtime_config(saved_config)

    task = AnalysisTask(obj, service_instance, analyst)
    task.config = AnalysisConfig(**saved_config)
    task.start()
    add_task(task)

    service_instance.set_task(task)

    if execute == 'process':
        __service_thread_pool__.apply_async(func=service_work_handler,
                                             args=(service_instance, final_config,))
    elif execute == 'thread':
        __service_thread_pool__.apply_async(func=service_work_handler,
                                            args=(service_instance, final_config,))
    elif execute == 'local':
        service_instance.execute(final_config)

    # Return after starting thread so web request can complete.
    result['success'] = True
    return result

def add_task(task):
    """
    Add a new task.
    """

    logger.debug("Adding task %s" % task)
    insert_analysis_results(task)

def run_triage(obj, user):
    """
    Run all services marked as triage against this top-level object.

    :param obj: The CRITs top-level object class.
    :type obj: Class which inherits from
               :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param user: The user requesting the services to be run.
    :type user: str
    """

    services = triage_services()
    for service_name in services:
        try:
            run_service(service_name,
                        obj._meta['crits_type'],
                        obj.id,
                        user,
                        obj=obj,
                        execute=settings.SERVICE_MODEL)
        except:
            pass
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
        return {'success': False, 'message': e}

def get_service_config(name):
    status = {'success': False}
    service = CRITsService.objects(name=name, status__ne="unavailable").first()
    if not service:
        status['error'] = 'Service "%s" is unavailable. Please review error logs.' % name
        return status

    config = service.config.to_dict()
    service_class = crits.services.manager.get_service_class(name)
    if not service_class:
        status['error'] = 'Service "%s" is unavilable. Please review error logs.' % name
        return status
    display_config = service_class.get_config_details(config)

    status['config'] = display_config
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

    config = service.config.to_dict()
    cfg_form, html = service_class.generate_config_form(config)
    # This isn't a form object. It's the HTML.
    status['form'] = html
    status['service'] = service

    if post_data:
        #Populate the form with values from the POST request
        form = cfg_form(post_data)
        if form.is_valid():
            try:
                service_class.parse_config(form.cleaned_data)
            except ServiceConfigError as e:
                service.status = 'misconfigured'
                service.save()
                status['config_error'] = str(e)
                return status

            result = update_config(name, form.cleaned_data, analyst)
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
    if not service:
        return None

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
                                        status="available")
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
                                        status="available")
    else:
        services = CRITsService.objects(run_on_triage=True)
    return [s.name for s in services]

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
    tdict['analysis_id'] = tdict['id']
    del tdict['id']
    ear.merge(arg_dict=tdict)
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
    for a in obj.analysis:
        if str(a.analysis_id) == task.task_id:
            found = True
            break

    if not found:
        logger.warning("Tried to update a task that didn't exist.")
        insert_analysis_results(task)
    else:
        # Otherwise, update it.
        ear = EmbeddedAnalysisResult()
        tdict = task.to_dict()
        tdict['analysis_id'] = tdict['id']
        del tdict['id']
        ear.merge(arg_dict=tdict)
        obj_class.objects(id=obj_id,
                          analysis__id=task.task_id).update_one(set__analysis__S=ear)


# The service pools need to be defined down here because the functions
# that are used by the services must already be defined.
# Initialize BOTH process and thread pools for backwards compatability since
# run_service() can be made to run in either process or thread mode. Ideally
# we should just need to initialize one of these.
__service_thread_pool__ = ThreadPool(processes=settings.SERVICE_POOL_SIZE)
