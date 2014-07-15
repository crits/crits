from StringIO import StringIO

from crits.events.event import Event
from crits.indicators.indicator import Indicator
from crits.core.crits_mongoengine import EmbeddedSource
from crits.core.class_mapper import class_from_type
from crits.core.handlers import does_source_exist

from cybox.objects.artifact_object import Artifact
from cybox.objects.address_object import Address
from cybox.objects.domain_name_object import DomainName
from cybox.objects.email_message_object import EmailMessage
from cybox.objects.file_object import File

from stix.core import STIXPackage

class STIXParserException(Exception):
    """
    General exception for STIX Parsing.
    """

    def __init__(self, message):
        self.message = message

class STIXParser():
    """
    STIX Parser class.
    """

    def __init__(self, data, analyst, method):
        """
        Instantiation of the STIXParser can take the data to parse, the analyst
        doing the parsing, and the method of data aquisition.

        :param data: The data to parse.
        :type data: str
        :param analyst: The analyst parsing the document.
        :type analyst: str
        :param method: The method of acquiring this data.
        :type method: str
        """

        self.data = data

        self.package = None

        self.source = EmbeddedSource() # source.name comes from the stix header.
        self.source_instance = EmbeddedSource.SourceInstance()
        # The reference attribute and appending it to the source is
        # done after the TAXII message ID is determined.
        self.source_instance.analyst = analyst
        self.source_instance.method = method
        self.information_source = None

        self.imported = [] # track items that are imported
        self.failed = [] # track STIX/CybOX items that failed import
        self.saved_artifacts = {}

    def parse_stix(self, reference=None, make_event=False, source=''):
        """
        Parse the document.

        :param reference: The reference to the data.
        :type reference: str
        :param make_event: Whether or not to create an Event for this document.
        :type make_event: bool
        :param source: The source of this document.
        :type source: str
        :raises: :class:`crits.standards.parsers.STIXParserException`

        Until we have a way to map source strings in a STIX document to
        a source in CRITs, we are being safe and using the source provided
        as the true source.
        """

        f = StringIO(self.data)
        self.package = STIXPackage.from_xml(f)
        f.close()
        if not self.package:
            raise STIXParserException("STIX package failure")

        stix_header = self.package.stix_header
        if stix_header and stix_header.information_source and stix_header.information_source.identity:
            self.information_source = stix_header.information_source.identity.name
            if self.information_source:
                info_src = "STIX Source: %s" % self.information_source
                if not reference:
                    reference = ''
                else:
                    reference += ", "
                reference += info_src
        if does_source_exist(source):
            self.source.name = source
        elif does_source_exist(self.information_source):
            self.source.name = self.information_source
        else:
            #TODO: this should do something useful
            return

        self.source_instance.reference = reference
        self.source.instances.append(self.source_instance)

        if make_event: # TODO update appropriately?
            event = Event.from_stix(stix_package=self.package, source=[self.source])
            try:
                event.save(username=self.source_instance.analyst)
                self.imported.append((Event._meta['crits_type'], event))
            except Exception, e:
                #TODO this should not be printing
                print e.message

        if self.package.indicators:
            self.parse_indicators(self.package.indicators)

        if self.package.observables and self.package.observables.observables:
            self.parse_observables(self.package.observables.observables)

    def parse_indicators(self, indicators):
        """
        Parse list of indicators.

        :param indicators: List of STIX indicators.
        :type indicators: List of STIX indicators.
        """
        for indicator in indicators: # for each STIX indicator
            for observable in indicator.observables: # get each observable from indicator (expecting only 1)
                try: # create CRITs Indicator from observable
                    obj = Indicator.from_cybox(observable.object_.properties, [self.source])
                    obj.add_source(self.source)
                    obj.save(username=self.source_instance.analyst)
                    self.imported.append((Indicator._meta['crits_type'], obj))
                except Exception, e: # probably caused by cybox object we don't handle
                    self.failed.append((e.message, observable)) # note for display in UI

    def parse_observables(self, observables):
        """
        Parse list of observables in STIX doc.

        :param observables: List of STIX observables.
        :type observables: List of STIX observables.
        """
        for obs in observables: # for each STIX observable
            if not obs.object_ or not obs.object_.properties:
                self.failed.append(("Item", obs)) # note for display in UI
                continue
            try: # try to create CRITs object from observable
                cls = self.get_crits_type(obs.object_.properties) # determine which CRITs class matches
                obj = cls.from_cybox(obs, [self.source])
                obj.add_source(self.source)
                obj.save(username=self.source_instance.analyst)
                self.imported.append((cls._meta['crits_type'], obj)) # use class to parse object
            except Exception, e: # probably caused by cybox object we don't handle
                self.failed.append((e.message, obs.object_.properties)) # note for display in UI

    def get_crits_type(self, c_obj):
        """
        Get the class that the given cybox object should be interpreted as during import.

        :param c_obj: A CybOX object.
        :type c_obj: An instance of one of the various CybOX object classes.
        :returns: The CRITs class to use to import the given CybOX object.
        """
        if isinstance(c_obj, Address):
            imp_type = "IP"
        elif isinstance(c_obj, DomainName):
            imp_type = "Domain"
        elif isinstance(c_obj, Artifact):
            imp_type = "RawData"
        elif isinstance(c_obj, File) and c_obj.custom_properties and c_obj.custom_properties[0].name == "crits_type" and c_obj.custom_properties[0]._value == "Certificate":
            imp_type = "Certificate"
        elif isinstance(c_obj, File) and self.has_network_artifact(c_obj):
            imp_type = "PCAP"
        elif isinstance(c_obj, File):
            imp_type = "Sample"
        elif isinstance(c_obj, EmailMessage):
            imp_type = "Email"
        else: # try to parse all other possibilities as Indicator
            imp_type = "Indicator"
        return class_from_type(imp_type)

    def has_network_artifact(self, file_obj):
        """
        Determine if the CybOX File object has a related Artifact of
        'Network' type.

        :param file_obj: A CybOX File object
        :return: True if the File has a Network Traffic Artifact
        """
        if not file_obj or not file_obj.parent or not file_obj.parent.related_objects:
            return False
        for obj in file_obj.parent.related_objects: # attempt to find data in cybox
            if isinstance(obj.properties, Artifact) and obj.properties.type_ == Artifact.TYPE_NETWORK:
                return True
        return False

    def relate_objects(self):
        """
        for now we are relating all objects to each other with a common
        relationship type that is most likely inaccurate. Need to get actual
        relationship out of the cybox document once we are storing it there.
        """
        finished_objects = []
        for obj in self.imported:
            if not finished_objects: # Prime the list...
                finished_objects.append(obj[1])
                continue

            for right in finished_objects:
                obj[1].add_relationship(right,
                                     rel_type="Related_To",
                                     analyst=self.source_instance.analyst)
            finished_objects.append(obj[1])

        for f in finished_objects:
            f.save(username=self.source_instance.analyst)


