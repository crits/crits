import ast
import datetime
import json
import logging
import copy

from django.http import HttpResponse
from multiprocessing import Process
from threading import Thread, local

try:
    from mongoengine.base import ValidationError
except ImportError:
    from mongoengine.errors import ValidationError

from multiprocessing.pool import Pool, ThreadPool

from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext

import crits.services

from crits.core.class_mapper import class_from_type, class_from_id
from crits.core.crits_mongoengine import json_handler
from crits.core.handlers import build_jtable, csv_export
from crits.core.handlers import jtable_ajax_list, jtable_ajax_delete
from crits.core.user_tools import user_sources
from crits.services.analysis_result import AnalysisResult, AnalysisConfig
from crits.services.analysis_result import EmbeddedAnalysisResultLog
from crits.services.core import ServiceConfigError, AnalysisTask
from crits.services.service import CRITsService

logger = logging.getLogger(__name__)

def generate_analysis_results_csv(request):
    """
    Generate a CSV file of the Analysis Results information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request,AnalysisResult)
    return response

def generate_analysis_results_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = AnalysisResult
    type_ = "analysis_result"
    mapper = obj_type._meta['jtable_opts']
    if option == "jtlist":
        # Sets display url
        details_url = mapper['details_url']
        details_url_key = mapper['details_url_key']
        fields = mapper['fields']
        response = jtable_ajax_list(obj_type,
                                    details_url,
                                    details_url_key,
                                    request,
                                    includes=fields)
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    if option == "jtdelete":
        response = {"Result": "ERROR"}
        if jtable_ajax_delete(obj_type,request):
            response = {"Result": "OK"}
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    jtopts = {
        'title': "Analysis Results",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits.services.views.%ss_listing' % type_,
                           args=('jtlist',)),
        'deleteurl': reverse('crits.services.views.%ss_listing' % type_,
                             args=('jtdelete',)),
        'searchurl': reverse(mapper['searchurl']),
        'fields': mapper['jtopts_fields'],
        'hidden_fields': mapper['hidden_fields'],
        'linked_fields': mapper['linked_fields'],
        'details_link': mapper['details_link'],
        'no_sort': mapper['no_sort']
    }
    jtable = build_jtable(jtopts,request)
    jtable['toolbar'] = [
    ]
    if option == "inline":
        return render_to_response("jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_,
                                   'button' : '%ss_tab' % type_},
                                  RequestContext(request))
    else:
        return render_to_response("%s_listing.html" % type_,
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_},
                                  RequestContext(request))

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


def run_service(name, type_, id_, user, obj=None,
                execute='local', custom_config={}, **kwargs):
    """
    Run a service.

    :param name: The name of the service to run.
    :type name: str
    :param type_: The type of the object.
    :type type_: str
    :param id_: The identifier of the object.
    :type id_: str
    :param user: The user running the service.
    :type user: str
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
    if type_ not in settings.CRITS_TYPES:
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
        obj = class_from_id(type_, id_)
        if not obj:
            result['html'] = 'Could not find object.'
            return result

    service = CRITsService.objects(name=name).first()
    if not service:
        result['html'] = "Unable to find service in database."
        return result

    # See if the object is a supported type for the service.
    if not service_class.supported_for_type(type_):
        result['html'] = "Service not supported for type '%s'" % type_
        return result

    # When running in threaded mode, each thread needs to have its own copy of
    # the object. If we do not do this then one thread may read() from the
    # object (to get the binary) and then the second would would read() without
    # knowing and get undefined behavior as the file pointer would be who knows
    # where. By giving each thread a local copy they can operate independently.
    #
    # When not running in thread mode this has no effect except wasted memory.
    local_obj = local()
    local_obj.obj = copy.deepcopy(obj)

    # Give the service a chance to check for required fields.
    try:
        service_class.valid_for(local_obj.obj)
        if hasattr(local_obj.obj, 'filedata'):
            if local_obj.obj.filedata.grid_id:
                # Reset back to the start so the service gets the full file.
                local_obj.obj.filedata.seek(0)
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

    form = service_class.bind_runtime_form(user, final_config)
    if form:
        if not form.is_valid():
            # TODO: return corrected form via AJAX
            result['html'] = str(form.errors)
            return result

        # If the form is valid, create the config using the cleaned data.
        final_config = db_config
        final_config.update(form.cleaned_data)

    logger.info("Running %s on %s, execute=%s" % (name, local_obj.obj.id, execute))
    service_instance = service_class(notify=update_analysis_results,
                                     complete=finish_task)

    # Give the service a chance to modify the config that gets saved to the DB.
    saved_config = dict(final_config)
    service_class.save_runtime_config(saved_config)

    task = AnalysisTask(local_obj.obj, service_instance, user)
    task.config = AnalysisConfig(**saved_config)
    task.start()
    add_task(task)

    service_instance.set_task(task)

    if execute == 'process':
        p = Process(target=service_instance.execute, args=(final_config,))
        p.start()
    elif execute == 'thread':
        t = Thread(target=service_instance.execute, args=(final_config,))
        t.start()
    elif execute == 'process_pool':
        if __service_process_pool__ is not None and service.compatability_mode != True:
            __service_process_pool__.apply_async(func=service_work_handler,
                                                 args=(service_instance, final_config,))
        else:
            logger.warning("Could not run %s on %s, execute=%s, running in process mode" % (name, local_obj.obj.id, execute))
            p = Process(target=service_instance.execute, args=(final_config,))
            p.start()
    elif execute == 'thread_pool':
        if __service_thread_pool__ is not None and service.compatability_mode != True:
            __service_thread_pool__.apply_async(func=service_work_handler,
                                                args=(service_instance, final_config,))
        else:
            logger.warning("Could not run %s on %s, execute=%s, running in thread mode" % (name, local_obj.obj.id, execute))
            t = Thread(target=service_instance.execute, args=(final_config,))
            t.start()
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
                        execute=settings.SERVICE_MODEL,
                        custom_config={})
        except:
            pass
    return


def add_result(object_type, object_id, analysis_id, result, type_, subtype,
               analyst):
    """
    add_results wrapper for a single result.

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
    
    return add_results(object_type, object_id, analysis_id, [result], [type_],
                      [subtype], analyst)


def add_results(object_type, object_id, analysis_id, result, type_, subtype,
               analyst):
    """
    Add multiple results to an analysis task.

    :param object_type: The top-level object type.
    :type object_type: str
    :param object_id: The ObjectId to search for.
    :type object_id: str
    :param analysis_id: The ID of the task to update.
    :type analysis_id: str
    :param result: The list of result to append.
    :type result: list of str
    :param type_: The list of result types.
    :type type_: list of str
    :param subtype: The list of result subtypes.
    :type subtype: list of str
    :param analyst: The user updating the results.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    res = {'success': False}
    if not object_type or not object_id or not analysis_id:
        res['message'] = "Must supply object id/type and analysis id."
        return res

    # Validate user can add service results to this TLO.
    klass = class_from_type(object_type)
    sources = user_sources(analyst)
    obj = klass.objects(id=object_id, source__name__in=sources).first()
    if not obj:
        res['message'] = "Could not find object to add results to."
        return res

    if not(result and type_ and subtype):
        res['message'] = "Need a result, type, and subtype to add a result."
        return res

    if not(len(result) == len(type_) == len(subtype)):
        res['message'] = "result, type, and subtype need to be the same length."
        return res

    # Update analysis results
    final_list = []
    for key, r in enumerate(result):
        final = {}
        final['subtype'] = subtype[key]
        final['result'] = r
        tmp = ast.literal_eval(type_[key])
        for k in tmp:
            final[k] = tmp[k]
        final_list.append(final)

    ar = AnalysisResult.objects(analysis_id=analysis_id).first()
    if ar:
        AnalysisResult.objects(id=ar.id).update_one(push_all__results=final_list)
        
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

    # Validate user can add service results to this TLO.
    klass = class_from_type(object_type)
    sources = user_sources(analyst)
    obj = klass.objects(id=object_id, source__name__in=sources).first()
    if not obj:
        results['message'] = "Could not find object to add results to."
        return results

    # Update analysis log
    le = EmbeddedAnalysisResultLog()
    le.message = log_message
    le.level = level
    le.datetime = str(datetime.datetime.now())
    ar = AnalysisResult.objects(analysis_id=analysis_id).first()
    if ar:
        AnalysisResult.objects(id=ar.id).update_one(push__log=le)
        results['success'] = True
    else:
        results['message'] = "Could not find task to add log to."
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

    # Validate user can add service results to this TLO.
    klass = class_from_type(object_type)
    sources = user_sources(analyst)
    obj = klass.objects(id=object_id, source__name__in=sources).first()
    if not obj:
        results['message'] = "Could not find object to add results to."
        return results

    # Update analysis log
    date = str(datetime.datetime.now())
    ar = AnalysisResult.objects(analysis_id=analysis_id).first()
    if ar:
        AnalysisResult.objects(id=ar.id).update_one(set__status=status,
                                                    set__finish_date=date)
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
        status['form'] = ''
        status['service'] = ''
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

def delete_analysis(task_id, analyst):
    """
    Delete analysis results.
    """

    ar = AnalysisResult.objects(id=task_id).first()
    if ar:
        ar.delete(username=analyst)

def insert_analysis_results(task):
    """
    Insert analysis results for this task.
    """

    ar = AnalysisResult()
    tdict = task.to_dict()
    tdict['analysis_id'] = tdict['id']
    del tdict['id']
    ar.merge(arg_dict=tdict)
    ar.save()

def update_analysis_results(task):
    """
    Update analysis results for this task.
    """

    # If the task does not currently exist for the given sample in the
    # database, add it.

    found = False
    ar = AnalysisResult.objects(analysis_id=task.task_id).first()
    if ar:
        found = True

    if not found:
        logger.warning("Tried to update a task that didn't exist.")
        insert_analysis_results(task)
    else:
        # Otherwise, update it.
        tdict = task.to_dict()
        tdict['analysis_id'] = tdict['id']
        del tdict['id']

        #TODO: find a better way to do this.
        new_dict = {}
        for k in tdict.iterkeys():
            new_dict['set__%s' % k] = tdict[k]
        AnalysisResult.objects(id=ar.id).update_one(**new_dict)

# The service pools need to be defined down here because the functions
# that are used by the services must already be defined.
if settings.SERVICE_MODEL == 'thread_pool':
    __service_thread_pool__ = ThreadPool(processes=settings.SERVICE_POOL_SIZE)
    __service_process_pool__ = None
elif settings.SERVICE_MODEL == 'process_pool':
    __service_thread_pool__ = None
    __service_process_pool__ = Pool(processes=settings.SERVICE_POOL_SIZE)
else:
    __service_thread_pool__ = None
    __service_process_pool__ = None
