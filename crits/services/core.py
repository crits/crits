from datetime import datetime
from distutils.version import StrictVersion
import hashlib
from importlib import import_module
import logging
import os.path
import shutil
import sys
import tempfile
from multiprocessing import Process
from threading import Thread
import uuid

from django.conf import settings

from crits.core.crits_mongoengine import EmbeddedAnalysisResult, AnalysisConfig
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
                # If this is a subclass of Service but not an actual service,
                # (i.e. DatabaseService), call this function recursively.
                self._register_services(service_class)
                continue

            service_name = service_class.name
            service_version = service_class.version
            service_description = service_class.description
            supported_types = service_class.supported_types

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

                svc_obj.description = service_description
                svc_obj.version = service_version
                svc_obj.supported_types = supported_types
                svc_obj.save()
                self._services[service_class.name] = service_class

    def get_service_class(self, service_name):
        """
        Get a service class.

        :param service_name: The name of the service to get the class for.
        :type service_name: str
        :returns: Service class.
        """

        return self._services.get(service_name, None)

    @property
    def enabled_services(self):
        """
        A list of names of enabled services.

        This should be overridden by subclasses which allow users to enable
        and disable services.
        """

        # Return all services, since there's no concept of enabled/disabled.
        return self._services.keys()

    @property
    def triage_services(self):
        """
        A list of names of services set to run for "triage".

        This should be overridden by subclasses which allow users to specify
        which services run for triage.
        """

        # Return all services, since there's no concept of "triage" services.
        return self.enabled_services


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
        }

    def __str__(self):
        return "%s {Service: %s, Id: %s}" % (
            self.task_id, self.service.name, self.obj.id)


class AnalysisEnvironment(object):
    """
    AnalysisEnvironment class.
    """

    def __init__(self, manager, source, dest):
        self.manager = manager
        self.source = source
        self.dest = dest

    def run_all(self, obj):
        """
        Run all services on an object.

        :param obj: The CRITs object.
        :type obj: A CRITs object.
        """

        logger.info("Analyzing %s" % obj.id)
        for service_name in self.manager.services:
            self.run_service(service_name, obj)


class Service(object):
    """
    An abstract class to perform analysis on a sample.

    Subclasses must define the following class-level fields:
    - name
    - version

    If needed, subclasses SHOULD define a class-level `default_config` list
    of `ServiceConfigOption`s. These options may be overridden for a particular
    instance of a service when it is instantiated.

    The service class's docstring is used as a description for the service.

    Subclasses must define a function:
        def _scan(self, obj, config):
    This function should:
    - call `_add_result` with any dict or other object convertible to a dict,
    - call `_add_file` with new files to be added.
    - call `_debug`, `_info`, `_warning`, `_error`, `_critical` as appropriate.
    """

    TYPE_UNARCHIVER = "unarchiver"
    TYPE_UNPACKER = "unpacker"
    TYPE_CUSTOM = "custom_tool"
    TYPE_AV = "antivirus"

    source = settings.COMPANY_NAME

    # Can override and set to (i.e.) "comparison"
    purpose = "analysis"

    # Set to a list of 'Sample', 'PCAP', etc.
    supported_types = ['all']

    # Change to, i.e. ['md5'] if only a hash is needed.
    required_fields = ['filedata']

    # Override this to add configuration options
    default_config = []

    # use a custom template for results
    template = None

    # whether or not this service can be rerun by default (without force)
    rerunnable = False

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

    @staticmethod
    def generate_config_form(name, config):
        """
        Generate a form and HTML for configuration.

        This should be overridden by subclasses.
        """
        return None, None

    @staticmethod
    def validate_runtime(config, db_config):
        """
        Validate runtime configuration.

        this shoul dbe overridden by subclasses.
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
    def bind_runtime_form(analyst, config, data):
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

    def finalize(self):
        self._info("Analysis complete")
        # Only add files as "results" after the analysis has completed.
        # This will make them appear at the bottom of "results"
        for f in self.current_task.files:
            filename = f['filename']
            md5 = f['md5']
            self._add_result("file_added", filename, {'md5': md5})
        for f in self.current_task.certificates:
            filename = f['filename']
            md5 = f['md5']
            self._add_result("cert_added", filename, {'md5': md5})
        for f in self.current_task.pcaps:
            filename = f['filename']
            md5 = f['md5']
            self._add_result("pcap_added", filename, {'md5': md5})
        logger.debug("Finishing analysis on %s" % self.current_task)
        self.current_task.finish()

    def execute(self, config):
        """
        Execute an analysis task.
        """

        self.config = config
        self.ensure_current_task()
        self._info("Starting Analysis")

        # Do it!
        try:
            self.scan(self.current_task.obj, config)
            # If a service is distributed, we expect it to handle its own result
            # additions, log messages, and task completion. If it is not
            # distributed, handle it for them.
            if not self.distributed:
                self.finalize()
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
                self.complete(self.current_task)
            # Reset current_task so another task can be assigned.
            self.current_task = None

    def ensure_current_task(self):
        """
        Make sure there is a current task for this service.
        """

        if self.current_task is None:
            raise Exception("No current task")

    def scan(self, obj, config):
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

        This does NOT consider whether a particular item has been analyzed
        before; the logic for that is done by the AnalysisEnvironment.

        Arguments:
        - obj: The object being considered for analysis.
        """

        return True

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
        log = EmbeddedAnalysisResult.EmbeddedAnalysisResultLog()
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
        for key in data:
            r[key] = data[key]
        self.current_task.results.append(r)

    def _add_file(self, data, filename=None, log_msg=None, relationship=None,
                  collection='Sample'):
        """
        Adds a new sample to the result set.

        These are not processed immediately, but instead queued until the rest
        of the analysis is done. This prevents an infinite recursion of new
        samples blocking completion of an analysis task. Instead, it creates a
        log entry.

        Services should not call `_add_result()` to indicate that they added a
        file. This is handled after the service has completed analysis.

        Also, services should not separately log that they have added a file.
        The `log_msg` is automatically logged at the INFO level (self._info()).
        `log_msg` may contain a single "{0}", which is replaced by the MD5 hash
        of `data`.
        """

        self.ensure_current_task()

        # If a service does not specify a filename for this new file,
        # use a combination of the original file's name and the service name.
        if not filename:
            filename = "{0}.{1.obj.id}.{1.service.name}".format(collection, self.current_task)
        file_md5 = hashlib.md5(data).hexdigest()
        f = {'data': data,
             'filename': filename,
             'md5': file_md5,
             'relationship': relationship}
        if collection == 'Sample':
            self.current_task.files.append(f)
        elif collection == 'Certificate':
            self.current_task.certificates.append(f)
        elif collection == 'PCAP':
            self.current_task.pcaps.append(f)
        else:
            return

        if not log_msg:
            log_msg = "Added new %s with MD5 {0}" % collection

        if '{0}' in log_msg:
            log_msg = log_msg.format(file_md5)

        self._info(log_msg)


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


# XXX: ALL THIS CAN BE REMOVED!
class ServiceConfigOption(object):
    """
    A configurable option for services.
    """

    STRING = "string"
    INT = "integer"
    BOOL = "boolean"
    LIST = "list"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    PASSWORD = "password"

    def __init__(self, name, type_, description="", default=None,
                    required=False, private=False, choices=None,
                    runtime_only=False):
        self.name = name
        self.type_ = type_
        self.runtime_only = runtime_only
        self.description = description.strip()
        if default is None:
            if type_ == ServiceConfigOption.STRING:
                self.default = ""
            elif type_ == ServiceConfigOption.INT:
                self.default = 0
            elif type_ == ServiceConfigOption.BOOL:
                self.default = True
            elif type_ == ServiceConfigOption.LIST:
                self.default = []
            elif type_ == ServiceConfigOption.SELECT:
                self.default = ""
            elif type_ == ServiceConfigOption.MULTI_SELECT:
                self.default = []
            elif type_ == ServiceConfigOption.PASSWORD:
                self.default = ""

            else:
                msg = "Unknown Config Option Type: {0}".format(type_)
                raise ValueError(msg)
        else:
            self.default = default

        if type_ in (ServiceConfigOption.SELECT,
                     ServiceConfigOption.MULTI_SELECT):
            if not choices:
                raise ServiceConfigError("Must provide choices")
            self.choices = choices

        if type_ == ServiceConfigOption.SELECT:
            # SELECT options are automatically required.
            self.required = True
        else:
            self.required = required
        self.private = private

    def format_value(self, value, printable=True):
        """
        Formats an option value for output.

        - INT, BOOL, and STRING values are left as is.
        - LIST values are converted to a newline-delimited string.
        - If `printable` is False, then SELECT and MULTI_SELECT are left as
          their indicies, otherwise they are converted to printable strings.
        """

        if self.type_ == ServiceConfigOption.LIST and isinstance(value, list):
            return "\n".join(value)
        elif self.type_ == ServiceConfigOption.SELECT and printable:
            if not value:
                return ""
            return self.choices[int(value) - 1]
        elif self.type_ == ServiceConfigOption.MULTI_SELECT and printable:
            if not value:
                return ""
            try:
                return "\n".join([self.choices[int(x) - 1] for x in value])
            except:
                return "\n".join(x for x in value)
        else:
            return value

    def parse_value(self, value):
        """
        Parse a config value from a form into the correct representation.
        """

        if (self.type_ == ServiceConfigOption.LIST and not
                isinstance(value, list)):
            # Remove empty lines.
            return [x.strip() for x in value.split("\n") if x.strip()]
        elif self.type_ == ServiceConfigOption.SELECT:
            if not value:
                return ""
            return int(value)
        elif self.type_ == ServiceConfigOption.MULTI_SELECT:
            if not value:
                return []
            return [int(x) for x in value]
        else:
            return value

    def replace_value(self, value):
        """
        Replace an index-based value with its true value.
        """

        if self.type_ == ServiceConfigOption.SELECT:
            return self.choices[int(value) - 1]
        elif self.type_ == ServiceConfigOption.MULTI_SELECT:
            return list([self.choices[int(x) - 1] for x in value])
        else:
            return value

    def enumerate_choices(self):
        return list(enumerate(self.choices, start=1))

    def __repr__(self):
        return ("%s('%s', '%s', description='%s', default='%s', "
                "required=%s, private=%s)" %
                (self.__class__.__name__, self.name, self.type_,
                 self.description, self.default, self.required, self.private))
