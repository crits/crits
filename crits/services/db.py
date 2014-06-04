import inspect
import logging

from bson.objectid import ObjectId
from distutils.version import StrictVersion
from mongoengine.base import ValidationError

from crits.certificates.certificate import Certificate
from crits.core.class_mapper import class_from_type, class_from_id
from crits.core.crits_mongoengine import EmbeddedAnalysisResult, AnalysisConfig
from crits.domains.domain import Domain
from crits.events.event import Event
from crits.indicators.indicator import Indicator
from crits.ips.ip import IP
from crits.pcaps.pcap import PCAP
from crits.raw_data.raw_data import RawData
from crits.samples.sample import Sample
from crits.services.core import (AnalysisSource, AnalysisDestination, Service,
        ServiceManager, ServiceConfigError, ServiceUnavailableError)
from crits.services.service import CRITsService

logger = logging.getLogger(__name__)


class DatabaseService(Service):
    """
    Database service class.
    """

    def __init__(self, config, notify=None, complete=None):
        super(DatabaseService, self).__init__(config, notify, complete)

    def _fetch_meta(self, query_filter, result_filter):
        """
        Fetch sample metadata.

        :param query_filter: The filter to use to find the sample.
        :type query_filter: dict
        :param result_filter: Limit the result to these fields.
        :type result_filter: tuple
        :returns: :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        """

        self.ensure_current_task()

        results = Sample.objects(__raw__=query_filter).only(*result_filter)
        return results


class DatabaseServiceManager(ServiceManager):
    """
    Database Service Manager class.
    """

    def __init__(self, services_package=None):
        super(DatabaseServiceManager, self).__init__(services_package)
        self._instantiate_collection()
        self._update_status_all()

    def reset_all(self):
        """
        Recreate the services collection.
        """

        logger.debug("Dropping service collection")
        CRITsService.drop_collection()
        self._instantiate_collection()
        self._update_status_all()

    def _update_status_all(self):
        """
        Ensure services are configured properly.
        """

        all_services = CRITsService.objects()
        for service in all_services:
            if 'name' not in service.to_dict():
                logger.warning("Invalid Service in Collection")
                logger.debug(service)
                continue

            self._update_status(service)

    def update_status(self, service_name):
        """
        Look up a service, and verify it is configured correctly
        """

        service = CRITsService.objects(name=service_name).first()
        self._update_status(service)

    def _update_status(self, service):
        """
        Update the status of a service.

        The status will be set to one of:
        - "available" if the service's python module was imported successfully
          and the service's config is successfully validated.
        - "misconfigured" if the service's python module was imported
          successfully, but it is not configured correctly.
        - "unavailable" if the service's python module had errors when
          importing or was not found.

        If a service is not "available", it will be disabled and removed
        from the triage list.
        """

        service_name = service.name
        config = service.config

        updates = {}

        try:
            service_class = self.get_service_class(service_name)
        except ServiceUnavailableError:
            logger.warning("Service %s is unavailable" % service_name)
            service.status = "unavailable"
            service.enabled = False
            service.run_on_triage = False
        else:
            try:
                service_class.validate(config.to_dict())
            except (ServiceConfigError, Exception):
                #TODO: shouldn't have to catch blanket exception here.
                logger.exception("Service %s is misconfigured" % service_name)
                service.status = "misconfigured"
                service.enabled = False
                service.run_on_triage = False
            else:
                service.status = "available"
                # Don't modify enabled or triage

        try:
            service.save()
        except ValidationError:
            logger.warning("Failed to update status for Service %s: %s" %
                           (service_name, updates))

    def _instantiate_collection(self):
        """
        Save services information in a Mongo collection.
        """

        logger.debug("Storing service metadata")
        for service_class in self._services.values():
            #If not already in collection
            current = CRITsService.objects(name=service_class.name).first()

            if not current:
                # Add the new service
                self._add_to_collection(service_class)

            else:
                logger.debug("Service %s already exists, checking version." \
                             % service_class.name)

                # Check the current version
                logger.debug('New version: %s -- Old version: %s' \
                             % (service_class.version, current.version))

                if (StrictVersion(service_class.version) !=
                        StrictVersion(current['version'])):
                    self._update_service(service_class)

    def _update_service(self, service_class):
        """
        Update a service in the database.
        """

        logger.info("Updating service %s in MongoDB" % service_class.name)

        new_config = service_class.build_default_config()
        current = CRITsService.objects(name=service_class.name).first()
        if current:
            current_config = current.config.to_dict()

        # Log removed keys
        removed_keys = set(current_config.keys()) - set(new_config.keys())
        if removed_keys:
            logger.warning("Old service configuration options removed: %s" %
                           str(removed_keys))

        # Log added keys
        added_keys = set(new_config.keys()) - set(current_config.keys())
        if added_keys:
            logger.warning("New service configuration options added: %s" %
                           str(added_keys))

        # All new items need to be added to the current config
        for key in added_keys:
            current_config[key] = new_config[key]

        current.config = AnalysisConfig(**current_config)

        # Update the version number
        current.version = service_class.version

        try:
            current.save()
            logger.info('Updated service %s successfully' % service_class.name)
        except:
            logger.warning('Failed to update service %s' % service_class.name)

    def _add_to_collection(self, service_class):
        """
        Add a service to the database.
        """

        logger.info("Adding service %s to MongoDB" % service_class.name)
        description = inspect.getdoc(service_class)

        config = service_class.build_default_config()
        config = AnalysisConfig(**config)
        new_service = CRITsService()
        new_service.name = service_class.name
        new_service.version = service_class.version
        new_service.service_type = service_class.type_
        new_service.purpose = service_class.purpose
        new_service.rerunnable = service_class.rerunnable
        new_service.supported_types = service_class.supported_types
        new_service.required_fields = service_class.required_fields
        new_service.enabled = False
        new_service.run_on_triage = False
        new_service.description = description
        new_service.config = config

        try:
            new_service.save()
            logger.debug('Added service %s successfully.' % service_class.name)
        except ValidationError, e:
            logger.warning('Failed to add service %s: %s' % (service_class.name,
                                                             e))

    def reset_config(self, service_name, analyst):
        """
        Reset the configuration for a service.
        """

        config = self.get_service_class(service_name).build_default_config()
        return self.update_config(service_name, config, analyst)

    def update_config(self, service_name, config, analyst):
        """
        Update the configuration for a service.
        """

        service = CRITsService.objects(name=service_name).first()
        service.config = AnalysisConfig(**config)
        try:
            service.save(username=analyst)
            self.update_status(service_name)
            return {'success': True}
        except ValidationError, e:
            return {'success': False,
                    'message': e}

    def get_config(self, service_name):
        """
        Get the configuration for a service.
        """

        service = CRITsService.objects(name=service_name).first()
        try:
            return service.config
        except Exception, e:
            logger.exception(e)
            return self.get_service_class(service_name).build_default_config()

    def set_enabled(self, service_name, enabled=True, analyst=None):
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
            return {'success': True}
        except ValidationError, e:
            return {'success': False,
                    'message': e}

    def set_triage(self, service_name, enabled=True, analyst=None):
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
            return {'success': True}
        except ValidationError, e:
            return {'success': False,
                    'message': e}

    @property
    def enabled_services(self):
        """
        Return names of services which are both available and enabled.
        """

        services = CRITsService.objects(enabled=True)
        return [s.name for s in services if s.name in self._services]

    def get_supported_services(self, crits_type, data_exists):
        """
        Get the supported services for a type.
        """

        #This is a temporary solution (only checks if 'data' is required).
        for s in self.enabled_services:
            cls = self.get_service_class(s)
            if ((cls.supported_types == 'all' or
                 crits_type in cls.supported_types) and
                 (data_exists or 'data' not in cls.required_fields)):
                yield s

    @property
    def triage_services(self):
        """
        Return names of available services set to run on triage.
        """

        # TODO: This doesn't care if the service is enabled, should it?
        # What is the correct behavior when enabled=False, run_on_triage=True?
        services = CRITsService.objects(run_on_triage=True)
        return [s.name for s in services if s.name in self._services]


class DatabaseAnalysisSource(AnalysisSource):
    """
    Use the CRITs MongoDB database to retrieve files to analyze.
    """
    pass

class DatabaseAnalysisDestination(AnalysisDestination):
    """
    Use the CRITs MongoDB database to save results.
    """

    def results_exist(self, service_class, obj):
        """
        Check to see if analysis results exist for this service.
        """

        return self._analysis_exists(obj,
                                     service_class.name,
                                     service_class.version)

    def add_task(self, task):
        """
        Add a new task.
        """

        logger.debug("Adding task %s" % task)
        self._insert_analysis_results(task)

    def update_task(self, task):
        """
        Update an existing task.
        """

        logger.debug("Updating task %s" % task)
        self._update_analysis_results(task)

    def finish_task(self, task):
        """
        Finish a task.
        """

        logger.debug("Finishing task %s" % task)
        self.update_task(task)

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

    def delete_analysis(self, crits_type, identifier, task_id, analyst):
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

    def _insert_analysis_results(self, task):
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

    def _update_analysis_results(self, task):
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
            self._insert_analysis_results(task)
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

    def _analysis_exists(self, obj, service_name, version=None):
        """
        Check for existing analysis results

        If the item of `crits_type` identified by `identifier` contains an
        analysis result produced by service_name, return True. If version is
        specified, only return True if there is an existing analysis result
        using this version or later.
        """

        obj_class = class_from_type(obj._meta['crits_type'])
        obj = obj_class.objects(id=obj.id).first()
        if obj:
            for analysis in obj.analysis:
                if analysis.service_name == service_name:
                    if version is None:
                        return True
                    try:
                        result_version = StrictVersion(analysis.version)
                    except:
                        result_version = 0
                    if result_version >= version:
                        return True
        return False
