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


class ServiceUnavailableError(Exception):
    pass


class ServiceConfigError(Exception):
    pass


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
                if not svc_obj:
                    svc_obj = CRITsService()
                    svc_obj.name = service_name
                    if hasattr(service_class, 'get_config'):
                        try:
                            new_config = service_class().get_config({})
                            svc_obj.config = AnalysisConfig(**new_config)
                        except ServiceConfigError:
                            svc_obj.status = "misconfigured"
                            msg = ("Service %s is misconfigured." %
                                   service_name)
                            logger.warning(msg)
                else:
                    if hasattr(service_class, 'get_config'):
                        existing_config = svc_obj.config.to_dict()
                        try:
                            new_config = service_class().get_config(existing_config)
                            svc_obj.config = AnalysisConfig(**new_config)
                        except ServiceConfigError:
                            svc_obj.status = "misconfigured"
                            msg = ("Service %s is misconfigured." %
                                   service_name)
                            logger.warning(msg)
                svc_obj.description = service_description
                svc_obj.version = service_version
                svc_obj.save()
                self._services[service_class.name] = service_class

    def get_service_class(self, service_name):
        """
        Get a service class.

        :param service_name: The name of the service to get the class for.
        :type service_name: str
        :returns: Service class.
        """

        try:
            return self._services[service_name]
        except KeyError:
            raise ServiceUnavailableError("Service is not available")

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


class AnalysisSource(object):
    pass

class AnalysisDestination(object):
    """
    Defines a location for handling the results of an analysis.

    There are four functions a subclass may override. Only `finish_task` is
    required.
    """

    def results_exist(self, service_class, obj):
        """
        Determine whether a service has been run on an object.

        The intent is to prevent duplicate analysis by services which have
        already been run on a given sample, so logic should probably not use
        the task_id for any comparisons.

        Unless overridden, the default return value is False, meaning that
        the analysis should be run.
        """

        return False

    def add_task(self, task):
        """
        Record the creation of a task, before it has actually started.

        The intent is for this to be used in applications which queue tasks
        or run them in the background. By default this function does nothing.
        """

        pass

    def update_task(self, task):
        """
        Called whenever a service wants to report an update.

        This can be used by long-running services to provide feedback to
        users (through an application that supports it). The default behavior
        is to do nothing.
        """

        pass

    def finish_task(self, task):
        """
        Called when a task has been finished.

        Subclasses must override this function.
        """

        raise NotImplementedError


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
            'rerunnable':           self.service.rerunnable,
            'distributed':          self.service.distributed,
            'version':              self.service.version,
            'type':                 self.service.type_,
            'config':               self.service.public_config,
            'analyst':              self.username,
            'id':                   self.task_id,
            'source':               self.source,
            'start_date':           self.start_date,
            'finish_date':          self.finish_date,
            'status':               self.status,
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

    def run_service(self, service_name, obj, analyst, execute='local',
                    force=False, custom_config=None):
        """
        Run a service.

        :param service_name: The name of the service to run.
        :type service_name: str
        :param obj: The CRITs object.
        :type obj: CRITs object.
        :param execute: The execution type.
        :type execute: str
        :param force: Force this service to run.
        :type force: bool
        :param custom_config: Use a custom configuration for this run.
        :type custom_config: dict
        """

        service_class = self.manager.get_service_class(service_name)

        # See if the object is a supported type for the service and that
        # all the required data is present. This should not be overridable by
        # a "Force" option
        if not service_class.supported_for_type(obj._meta['crits_type']):
            msg = "Service '%s' not supported for type '%s'" % (service_name,
                    obj._meta['crits_type'])
            logger.info(msg)
            raise ServiceAnalysisError(msg)

        if not service_class.obj_has_required_data(obj):
            msg = "Object does not have all required fields '%s'" % (
                    str(service_class.required_fields))
            logger.info(msg)
            raise ServiceAnalysisError(msg)

        if not force and not service_class.rerunnable:
            if self.dest.results_exist(service_class, obj):
                args = (service_name, service_class.version, obj.id)
                msg = ("Results for '%s' (v.%s) already exist for '%s'. Use "
                       "'force' to re-run." % args)
                logger.info(msg)
                raise ServiceAnalysisError(msg)

            if not service_class.valid_for(obj):
                msg = ("Service '%s' declined to run" % service_name)
                logger.info(msg)
                raise ServiceAnalysisError(msg)

        args = (service_name, obj.id, force, execute)
        logger.info("Running %s on %s, force=%s, execute=%s" % args)

        config = self.manager.get_config(service_name)
        config = config.to_dict()

        # Overwrite defaults with custom settings
        if custom_config:
            for key in custom_config:
                config[key] = custom_config[key]

        config = service_class.replace_config_values(config)

        notify_func = self.dest.update_task
        complete_func = self.dest.finish_task

        service_instance = service_class(config=config,
                                         notify=notify_func,
                                         complete=complete_func)

        task = AnalysisTask(obj, service_instance, analyst)
        task.start()
        self.dest.add_task(task)

        service_instance.set_task(task)

        if execute == 'process':
            p = Process(target=service_instance.execute)
            p.start()
        elif execute == 'thread':
            t = Thread(target=service_instance.execute)
            t.start()
        elif execute == 'local':
            service_instance.execute()

        # Return after starting thread so web request can complete.
        return


class Service(object):
    """
    An abstract class to perform analysis on a sample.

    Subclasses must define the following class-level fields:
    - name
    - version
    - type_

    If needed, subclasses SHOULD define a class-level `default_config` list
    of `ServiceConfigOption`s. These options may be overridden for a particular
    instance of a service when it is instantiated.

    The service class's docstring is used as a description for the service.

    Subclasses must define a function:
        def _scan(self, data, sample_dict):
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

    def execute(self):
        """
        Execute an analysis task.
        """

        self.ensure_current_task()
        self._info("Starting Analysis")

        # Do it!
        try:
            self._scan(self.current_task.obj)
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

    def _scan(self, data, sample_dict):
        """
        Perform the actual work of the service.

        Service subclasses should override this method.
        """

        raise NotImplementedError

    @classmethod
    def validate(cls, config):
        """
        Attempt to ensure a valid configuration for a service.

        Raises a ServiceConfigError if there is anything wrong.
        """

        cls._basic_validate(config)
        try:
            cls._validate(config)
        except ServiceConfigError:
            # Re-raise any ServiceConfigErrors
            raise
        except Exception as e:
            # Wrap any other Exceptions in a ServiceConfigError
            trace = sys.exc_info()[2]
            error = "%s: %s" % (e.__class__, e)
            raise ServiceConfigError(error), None, trace

    @classmethod
    def _basic_validate(cls, config):
        """
        Attempt to ensure a valid configuration for a service.

        Raises a ServiceConfigError if there is anything wrong.
        """

        default_keys = set([option.name for option in cls.default_config])
        config_keys = set(config.keys())

        missing_keys = default_keys - config_keys
        extra_keys = config_keys - default_keys

        #Ensure all settings in `default_config` are present in `config`
        if missing_keys:
            error = "Missing options: {%s}" % ", ".join(missing_keys)
            raise ServiceConfigError(error)

        # Ensure there are no extra settings
        if extra_keys:
            error = "Extra options: {%s}" % ", ".join(extra_keys)
            raise ServiceConfigError(error)

        for option in cls.default_config:
            # Ensure all required STRING options are non-empty
            if option.required and not config[option.name]:
                error = "Option must not be blank: %s" % option.name
                raise ServiceConfigError(error)

    @classmethod
    def _validate(cls, config):
        """
        Perform any service-specific configuration checks.

        Service subclasses can override this method. It should raise
        an Exception (either a ServiceConfigError or any other
        Exception class) to indicate a problem with the configuration.
        """

        pass

    @classmethod
    def build_default_config(cls):
        """
        Return a dictionary of key/value pairs based on `default_config`

        Uses the `name` and `default` value of each setting.
        """

        config = {}

        for option in cls.default_config:
            logger.debug(option)
            config[option.name] = option.default

        return config

    @property
    def public_config(self):
        """
        Return all the non-private config options for a service.
        """

        return self.__class__.get_public_config(self.config)

    @classmethod
    def get_public_config(cls, full_config):
        """
        Return a copy of full_config containting only non-private options.
        """

        config = {}

        for option in cls.default_config:
            key = option.name
            if not option.private and not option.runtime_only:
                config[key] = full_config[key]
            else:
                logger.debug("Omitting key %s" % key)

        return config

    @classmethod
    def format_config(cls, config, clean=False, printable=True,
                        private_string="[PRIVATE]"):
        """
        Format a config dictionary for display.

        The dictionary is converted to a list of (name, value) tuples, in order
        to preserve the intended order in a class's `default_config`.

        If `clean` is `True`, all config settings which are private will have
        their values replaced with the `private_string`.

        If the config setting is runtime_only it will be left out.
        """

        config_list = []

        # Preserve the ordering from cls.default_config
        for option in cls.default_config:
            key = option.name
            if clean and option.private:
                value = private_string
                logger.debug("Hiding value for private option %s" % key)
            elif option.runtime_only:
                continue
            else:
                value = config[key]
                value = option.format_value(value, printable=printable)
            logger.debug("key: %s, value: %s" % (key, value))
            config_list.append((key, value))

        return config_list

    @classmethod
    def parse_config(cls, incoming_config, exclude_private=False):
        """
        Parse a dict containing config options.

        Any necessary transformations are performed. Currently the only
        transformation is converting a newline-delimited string into a list,
        for config options of type ServiceConfigOption.LIST.
        """

        new_config = {}

        logger.debug("Parsing %s:" % cls.name)
        logger.debug(incoming_config)

        for option in cls.default_config:
            if option.private and exclude_private:
                continue
            key = option.name
            value = incoming_config.get(key, '')
            new_config[key] = option.parse_value(value)
            logger.debug("key: %s, ingoing: %s, outcoming: %s" %
                    (key,  value, new_config[key]))

        logger.debug("Done parsing %s" % cls.name)
        logger.debug(new_config)
        return new_config

    @classmethod
    def replace_config_values(cls, config):
        """
        Call replace_value on each value in config dictionary.
        """

        new_config = {}

        for option in cls.default_config:
            key = option.name
            new_config[key] = option.replace_value(config[key])

        return new_config

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

    @classmethod
    def obj_has_required_data(cls, obj):
        """
        Ensure the object has the required fields.
        """

        for field in cls.required_fields:
            # Field does not exist or is "false" (0, False, None, "", etc.)
            if not hasattr(obj, field) or not getattr(obj, field):
                return False
        return True

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
