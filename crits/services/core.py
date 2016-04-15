from datetime import datetime
from distutils.version import StrictVersion

try:
    from importlib import import_module
except ImportError:
    # Django < 1.7 and Python < 2.7
    from django.utils.importlib import import_module

import logging
import os.path
import shutil
import tempfile
import uuid

from django.conf import settings

from crits.services.analysis_result import EmbeddedAnalysisResultLog, AnalysisConfig
from crits.services.service import CRITsService

logger = logging.getLogger(__name__)


class ServiceConfigError(Exception):
    pass


#XXX: This can be removed when service_cli is not using it.
class ServiceAnalysisError(Exception):
    pass


class ServiceManager(object):
    """
    Discover, register, and configure Services.
    """

    def __init__(self, services_packages=None):
        """
        Create a new ServiceManager object.

        - `services_packages` should be a Python package containing a single
          directory for each available service. If not provided, it will use
          the package in which the ServiceManager class is defined.
        """

        self._services = {}

        if not services_packages:
            services_packages = settings.SERVICE_DIRS
        self._import_services(services_packages)
        self._register_services(Service)

    def _import_services(self, services_packages):
        """
        Load each module in the directory containing pkg

        This code assumes that each subdirectory in the directory containing
        `pkg` is a python module (containing an __init__.py file). This
        function will not automatically import other files within this
        directory or any subdirectories (though may if the __init__.py file
        imports them).
        """

        for services_pkgs in services_packages:
            if os.path.isdir(services_pkgs):
                for services_pkg in os.listdir(services_pkgs):
                    full_path = os.path.join(services_pkgs, services_pkg)
                    if (os.path.isdir(full_path) and
                        os.path.isfile(os.path.join(full_path, '__init__.py'))):
                        try:
                            import_module(services_pkg)
                        except ImportError as e:
                            logger.warning("Failed to import service (%s): %s" %
                                            (services_pkg, e))

    def _register_services(self, klass):
        """
        Create a dict with names of available services and classes that
        implement them.

        This is a recursive function since __subclasses__() only returns direct
        subclasses. If class A(object):, class B(A):, and class C(B):, then
        A.__subclasses__() doesn't contain C.

        All subclasses of the Service class are saved in the `services`
        dictionary. It is intended that each of these was imported by the
        _import_services function, but this is not enforced. The key in the
        dictionary is the `name` class-level field, and the value is the class
        itself. It is recommended that the service "example" be implemented
        in a class "ExampleService" defined in a module named
        "example_service", but this is not enforced, and the only string
        visible to the end-user/analyst is the service name.
        """

        for service_class in klass.__subclasses__():
            # TODO: replace this with a proper check for a valid service
            if not (hasattr(service_class, "name") and
                    hasattr(service_class, "version")):
                # If this is a subclass of Service but not an actual service
                # call this function recursively.
                self._register_services(service_class)
                continue

            service_name = service_class.name
            service_version = service_class.version
            service_description = service_class.description
            supported_types = service_class.supported_types
            compatability_mode = service_class.compatability_mode

            logger.debug("Found service subclass: %s version %s" %
                            (service_name, service_version))

            try:
                StrictVersion(service_version)
            except ValueError as e:
                # Unable to parse the service version
                msg = ("Service %s is invalid, and will not be available." %
                       service_name)
                logger.warning(msg)
                logger.warning(e)
                continue
            else:
                # Only register the service if it is valid.
                logger.debug("Registering Service %s" % service_name)
                svc_obj = CRITsService.objects(name=service_class.name).first()
                service = service_class()
                if not svc_obj:
                    svc_obj = CRITsService()
                    svc_obj.name = service_name
                    try:
                        new_config = service.get_config({})
                        svc_obj.config = AnalysisConfig(**new_config)
                    except ServiceConfigError:
                        svc_obj.status = "misconfigured"
                        msg = ("Service %s is misconfigured." % service_name)
                        logger.warning(msg)
                    else:
                        svc_obj.status = "available"
                else:
                    existing_config = svc_obj.config.to_dict()
                    try:
                        new_config = service.get_config(existing_config)
                        svc_obj.config = AnalysisConfig(**new_config)
                    except ServiceConfigError:
                        svc_obj.status = "misconfigured"
                        svc_obj.enabled = False
                        svc_obj.run_on_triage = False
                        msg = ("Service %s is misconfigured." % service_name)
                        logger.warning(msg)
                    else:
                        svc_obj.status = "available"
                # Give the service a chance to tell us what is wrong with the
                # config.
                try:
                    service.parse_config(svc_obj.config.to_dict())
                except ServiceConfigError as e:
                    svc_obj.status = "misconfigured"
                    svc_obj.enabled = False
                    svc_obj.run_on_triage = False

                svc_obj.description = service_description
                svc_obj.version = service_version
                svc_obj.supported_types = supported_types
                svc_obj.compatability_mode = compatability_mode
                svc_obj.save()
                self._services[service_class.name] = service_class
        # For anything in the database that did not import properly, mark the
        # status to unavailable.
        svcs = CRITsService.objects()
        for svc in svcs:
            if svc.name not in self._services:
                svc.status = 'unavailable'
                svc.enabled = False
                svc.run_on_triage = False
                svc.save()

    def get_service_class(self, service_name):
        """
        Get a service class.

        :param service_name: The name of the service to get the class for.
        :type service_name: str
        :returns: Service class.
        """

        return self._services.get(service_name, None)


class AnalysisTask(object):
    """
    AnalysisTask class.
    """

    # Fake enumeration for service status
    # TODO: Determine complete list of supported statuses.
    STATUS_CREATED = "created"
    STATUS_STARTED = "started"
    STATUS_ERROR = "error"
    STATUS_COMPLETED = "completed"

    STATUS_LIST = [STATUS_CREATED, STATUS_STARTED,
                   STATUS_ERROR, STATUS_COMPLETED]

    def __init__(self, obj, service, analyst):
        self.obj = obj
        # AnalysisTask.service should be an instance of a Service class.
        self.service = service

        #TODO: determine best type of ID
        self.task_id = str(uuid.uuid4())
        #TODO: Source is always 'None' for now until we figure out a better
        # way to handle it.
        self.source = None
        self.start_date = None
        self.finish_date = None
        self.status = None
        self.username = analyst

        self.log = []
        self.results = []
        self.files = []
        self.certificates = []
        self.pcaps = []

        self._set_status(AnalysisTask.STATUS_CREATED)

    def start(self):
        """
        Start a task.
        """

        self.start_date = str(datetime.now())
        self._set_status(AnalysisTask.STATUS_STARTED)

    def error(self):
        """
        Mark a task as errored.
        """

        self._set_status(AnalysisTask.STATUS_ERROR)

    def finish(self):
        """
        Finish a task.
        """

        self.finish_date = str(datetime.now())
        # If there were no errors during analysis, mark the task as completed.
        if self.status is not AnalysisTask.STATUS_ERROR:
            self._set_status(AnalysisTask.STATUS_COMPLETED)

    def _set_status(self, status):
        """
        Set the status of a task.

        :param status: The status to set.
        :type status: str
        :raises: ValueError
        """

        if status not in AnalysisTask.STATUS_LIST:
            raise ValueError("Invalid Status: %s" % status)
        self.status = status

    def to_dict(self):
        return {
            'service_name':         self.service.name,
            'template':             self.service.template,
            'distributed':          self.service.distributed,
            'version':              self.service.version,
            'analyst':              self.username,
            'id':                   self.task_id,
            'source':               self.source,
            'start_date':           self.start_date,
            'finish_date':          self.finish_date,
            'status':               self.status,
            'config':               self.config,
            'log':                  self.log,
            'results':              self.results,
            'object_type':          self.obj._meta['crits_type'],
            'object_id':            str(self.obj.id),
            'results':              self.results,
        }

    def __str__(self):
        return "%s {Service: %s, Id: %s}" % (
            self.task_id, self.service.name, self.obj.id)


class Service(object):
    """
    An abstract class to perform analysis on a TLO.

    Subclasses must define the following class-level fields:
    - name
    - version
    - description

    Subclasses must define a function:
        def run(self, obj, config):
    This function should:
    - call `_add_result` with any dict or other object convertible to a dict,
    - call `_debug`, `_info`, `_warning`, `_error`, `_critical` as appropriate.
    """

    source = settings.COMPANY_NAME

    # Set to a list of 'Sample', 'PCAP', etc.
    supported_types = ['all']

    # Change to, i.e. ['md5'] if only a hash is needed.
    required_fields = ['filedata']

    # Set to a boolean. Currently, if set to False then if the
    # settings.SERVICE_MODEL is thread_pool or process_pool, then the service
    # will instead run in thread or process respectively.
    compatability_mode = False

    # use a custom template for results
    template = None

    # whether or not this service is distributed.
    distributed = False

    def __init__(self, notify=None, complete=None):
        """
        Create a new service.

        - `notify` is a function that should be called to report on the
          progress of the current task.
        - `complete` is a function that should be called when current_task
          is done.
        """

        # Register callback functions
        self.notify = notify
        self.complete = complete

        self.current_task = None

    @staticmethod
    def parse_config(config):
        """
        Check a config for validity.

        This should be overridden by subclasses.
        """
        return config

    @staticmethod
    def get_config(existing_config):
        """
        Get configuration for this service. It takes the existing config
        from the database as a parameter so it can modify if necessary.

        This should be overridden by subclasses.
        """
        return existing_config

    @staticmethod
    def get_config_details(config):
        """
        Convert a service configuration for presentation.

        This should be overridden by subclasses.
        """
        return config

    @staticmethod
    def save_runtime_config(config):
        """
        Modify the configuration that is saved in the database for a run
        of the service.

        This should be overridden by subclasses.
        """
        pass

    @classmethod
    def generate_config_form(self, config):
        """
        Generate a form and HTML for configuration.

        This should be overridden by subclasses.
        """
        return None, None

    @staticmethod
    def validate_runtime(config, db_config):
        """
        Validate runtime configuration.

        This should be overridden by subclasses.
        """
        pass

    @classmethod
    def generate_runtime_form(self, analyst, config, crits_type, identifier):
        """
        Generate a form as HTML for runtime.

        This should be overridden by subclasses.
        """
        return None

    @staticmethod
    def bind_runtime_form(analyst, config):
        """
        Generate a form and bind it.

        This should be overridden by subclasses.
        """
        return None

    def set_task(self, task):
        """
        Set the current analysis task for this service.

        Multiple tasks can be passed sequentially to the same service. This
        allows callers to analyze multiple items with the same configuration.
        Services cannot currently manage multiple tasks at the same time. To
        parallelize, create multiple Service objects.
        """

        if self.current_task is not None:
            #TODO: return a better error code
            logger.error("Existing Task: %s" % self.current_task)
            raise Exception("Current task is not done")

        self.current_task = task

    def execute(self, config):
        """
        Execute an analysis task.
        """

        self.config = config
        self.ensure_current_task()
        self._info("Starting Analysis")

        # Do it!
        try:
            self.run(self.current_task.obj, config)
            # If a service is distributed, we expect it to handle its own result
            # additions, log messages, and task completion. If it is not
            # distributed, handle it for them.
            if not self.distributed:
                self.current_task.finish()
        except NotImplementedError:
            error = "Service not yet implemented"
            logger.error(error)
            self._error(error)
        except Exception, e:
            logger.exception("Error running service %s" % self.name)
            error = "Error running service: %s" % e
            self._error(error)
        finally:
            if self.complete:
                self._info("Analysis complete")
                from crits.services.handlers import update_analysis_results
                update_analysis_results(self.current_task)
                # Check status, if it is ERROR, don't change it.
                if self.current_task.status == self.current_task.STATUS_ERROR:
                    status = self.current_task.STATUS_ERROR
                else:
                    status = self.current_task.STATUS_COMPLETED
                self.complete(self.current_task.obj._meta['crits_type'],
                              str(self.current_task.obj.id),
                              self.current_task.task_id,
                              status,
                              self.current_task.username)
                logger.debug("Finished analysis %s" % self.current_task.task_id)
            # Reset current_task so another task can be assigned.
            self.current_task = None

    def ensure_current_task(self):
        """
        Make sure there is a current task for this service.
        """

        if self.current_task is None:
            raise Exception("No current task")

    def run(self, obj, config):
        """
        Perform the actual work of the service.

        Service subclasses should override this method.
        """

        raise NotImplementedError

    @staticmethod
    def valid_for(obj):
        """
        Determine whether a service is applicable to a given target.

        Services do not need to override this method if they want to be
        called for every object type. Otherwise, they may determine whether to
        run based on the members of the object.

        Typically, services should just call methods of CRITsBaseDocument, but
        services may implement their own decision logic.

        Arguments:
        - obj: The object being considered for analysis.
        """

        pass

    @classmethod
    def supported_for_type(cls, type_):
        """
        Ensure the service can run on this type.
        """

        return (cls.supported_types == 'all' or type_ in cls.supported_types)

    def _debug(self, msg):
        self._log('debug', msg)

    def _info(self, msg):
        self._log('info', msg)

    def _warning(self, msg):
        self._log('warning', msg)

    def _error(self, msg):
        self._log('error', msg)
        self.current_task.error()

    def _critical(self, msg):
        self._log('critical', msg)
        self.current_task.error()

    def _log(self, level, msg):
        """
        Add a log entry for this task.

        :param level: The log level for this entry.
        :type level: str ('debug', 'info', 'warning', 'error', 'critical')
        :param msg: The log message.
        :type msg: str
        """

        self.ensure_current_task()

        now = str(datetime.now())
        log = EmbeddedAnalysisResultLog()
        log.level = level
        log.message = msg
        log.datetime = now
        self.current_task.log.append(log)

    def _write_to_file(self):
        """
        Write data to a temporary file.
        """

        self.ensure_current_task()
        return TempAnalysisFile(self.current_task.obj)

    def _notify(self):
        """
        Send a notification if a notification function has been defined.
        """

        self.ensure_current_task()
        # If a `notify` function has been set, call it.
        if self.notify:
            self.notify(self.current_task)

    def _add_result(self, subtype, result, data=None):
        """
        Add another item to the list of results.

        Arguments:
        - subtype: A string representing what type of result this is. In some
          cases the same subtype may be used by different services.
        - result: The data that has been found. This should be a string
          suitable for direct comparison (pivoting) to locate other samples.
          This field is automatically rendered as a link to search for other
          samples containing an identical result
        - data: A dict containing other information associated with this
          result. By default these are not rendered as links, though this
          can be modified by a custom renderer.
        """

        self.ensure_current_task()

        if subtype is None:
            raise ValueError("subtype cannot be None")
        if result is None:
            raise ValueError("result cannot be None")
        if data is None:
            data = {}
        r = {}
        r['subtype'] = subtype
        r['result'] = result
        # Copy all of the other data into the result.
        r.update(data)
        #for key in data:
        #    r[key] = data[key]
        self.current_task.results.append(r)


    def _add_results(self, results=None):
        """
        Add a bunch of items to the list of results.

        Arguments:
        - results: The data that has been found. This should be formatted as described
          in _add_results with the subtype and result field already set
        """

        self.ensure_current_task()

        if results is None:
            raise ValueError("results cannot be None")

        self.current_task.results.extend(results)


class TempAnalysisFile(object):
    """
    Temporary Analysis File class.
    """

    def __init__(self, obj):
        self.obj = obj

    def __enter__(self):
        """
        Create the temporary file on disk.
        """

        tempdir = tempfile.mkdtemp()
        self.directory = tempdir
        tfile = os.path.join(tempdir, str(self.obj.id))
        with open(tfile, "wb") as f:
            f.write(self.obj.filedata.read())
        return tfile

    def __exit__(self, type, value, traceback):
        """
        Cleanup temporary file on disk.
        """

        if os.path.isdir(self.directory):
            shutil.rmtree(self.directory)
