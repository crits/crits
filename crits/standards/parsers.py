import base64
from hashlib import md5
from StringIO import StringIO
from mongoengine.queryset import Q

from crits.events.event import Event
from crits.samples.sample import Sample
from crits.emails.email import Email
from crits.indicators.indicator import Indicator
from crits.core.crits_mongoengine import EmbeddedSource
from crits.core.class_mapper import class_from_value
from crits.core.handlers import does_source_exist

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
        self.binding = None

        self.events = []
        self.samples = []
        self.emails = []
        self.indicators = []

        self.saved_artifacts = {}

        self.source = EmbeddedSource()
        # source.name comes from the stix header.
        self.source_instance = EmbeddedSource.SourceInstance()
        # The reference attribute and appending it to the source is
        # done after the TAXII message ID is determined.
        self.source_instance.analyst = analyst
        self.source_instance.method = method
        self.information_source = None

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
        (self.package, self.binding) = STIXPackage.from_xml(f)
        f.close()
        if not self.package and not self.binding:
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

        self.source_instance.reference = reference
        self.source.instances.append(self.source_instance)

        if make_event:
            event = Event.from_stix(stix_package=self.package, source=[self.source])
            try:
                event.save(username=self.source_instance.analyst)
            except Exception, e:
                print e.message
            self.events.append(('Event', str(event.id)))

        # Walk STIX indicators and pull out CybOX observables.
        # stix.(indicators|observables) is a list of CybOX observables
        if self.package.indicators:
            for indicator in self.package.indicators:
                if not indicator:
                    continue
                for observable in indicator.observables:
                    self.__parse_observable(observable)

        # Also walk STIX observables and pull out CybOX observables.
        # At some point the standard will allow stix_package.observables to be
        # an iterable object and we can collapse this with indicators.
        if self.package.observables:
            if self.package.observables.observables:
                for observable in self.package.observables.observables:
                    if not observable:
                        continue
                    self.__parse_observable(observable)

    def __parse_observable(self, observable):
        """
        Parse observable.

        :param observable: The observable to parse.
        :type observable: STIX observable
        """

        if observable.observable_composition:
            for obs in observable.observable_composition.observables:
                #print "observable composition"
                self.__parse_observable(obs)
        elif observable.object_:
            #print "stateful measure"
            self.__parse_object(observable.object_)
        elif observable.event:
            pass

    def __parse_object(self, obs_obj):
        """
        Parse an observable object.

        :param obs_obj: The observable object to parse.
        :type obs_obj: CybOX object type.
        """

        properties = obs_obj.properties
        type_ = properties._XSI_TYPE

        #would isinstance be preferable?
        #elif isinstance(defined_obj,
        #   cybox.objects.email_message_object.EmailMessage):
        #XXX: Need to check the database for an existing Sample or Indicator
        # and handle accordingly, or risk blowing it away!!!!
        if type_ == 'FileObjectType':
            sample = Sample.from_cybox(properties, [self.source])
            md5_ = sample.md5
            # do we already have this sample?
            db_sample = Sample.objects(md5=md5_).first()
            if db_sample:
                # flat out replacing cybox sample object with one from db.
                # we add the source to track we got a copy from TAXII.
                # if we have a metadata only doc, the add_file_data below
                # will generate metadata for us.
                sample = db_sample
                sample.add_source(self.source)
            if md5_ in self.saved_artifacts:
                (saved_obj, data) = self.saved_artifacts[md5_]
                if saved_obj._XSI_TYPE == 'FileObjectType':
                    #print "Only File found in SA"
                    return
                elif saved_obj._XSI_TYPE == 'ArtifactObjectType':
                    #print "Found matching Artifact in SA"
                    sample.add_file_data(data)
                    sample.save(username=self.source_instance.analyst)
                    self.samples.append(('Sample', sample.md5))
                    del self.saved_artifacts[md5_]
            else:
                #print "Saving File to SA"
                self.saved_artifacts[md5_] = (properties, None)
        elif type_ == 'EmailMessageObjectType':
            # we assume all emails coming in from TAXII are new emails.
            # there is no way to guarantee we found a dupe in the db.
            email = Email.from_cybox(properties, [self.source])
            email.save(username=self.source_instance.analyst)
            self.emails.append(('Email', str(email.id)))
        elif type_ in ['URIObjectType', 'AddressObjectType']:
            indicator = Indicator.from_cybox(properties, [self.source])
            ind_type = indicator.ind_type
            value = indicator.value
            db_indicator = Indicator.objects(Q(ind_type=ind_type) & Q(value=value)).first()
            if db_indicator:
                # flat out replacing cybox indicator object with one from db.
                # we add the source to track we got a copy from TAXII.
                indicator = db_indicator
                indicator.add_source(self.source)
            indicator.save(username=self.source_instance.analyst)
            self.indicators.append(('Indicator', str(indicator.id)))
        elif type_ == 'ArtifactObjectType':
            # XXX: Check properties.type_ to see if it is TYPE_FILE,
            # TYPE_MEMORY, from CybOX definitions. This isn't implemented
            # yet in Greg's code. Just parse the file blindly for now.
            #if properties.type_ == 'File':
            #    sample = Sample.from_cybox(properties, [self.source])
            #else:
            #    print "XXX: got unknown artifact type %s" % properties.type_
            data = base64.b64decode(properties.data)
            md5_ = md5(data).hexdigest()
            #print "Found Artifact"
            if md5_ in self.saved_artifacts:
                (saved_obj, data) = self.saved_artifacts[md5_]
                if saved_obj._XSI_TYPE == 'ArtifactObjectType':
                    #print "Only Artifact found in SA"
                    return
                elif saved_obj._XSI_TYPE == 'FileObjectType':
                    #print "Found matching File in SA"
                    sample = Sample.from_cybox(saved_obj, [self.source])
                    db_sample = Sample.objects(md5=md5_).first()
                    if db_sample:
                        # flat out replacing cybox sample object with one from db.
                        # we add the source to track we got a copy from TAXII.
                        # if we have a metadata only doc, the add_file_data below
                        # will generate metadata for us.
                        sample = db_sample
                        sample.add_source(self.source)
                    sample.add_file_data(data)
                    sample.save(username=self.source_instance.analyst)
                    self.samples.append(('Sample', sample.md5))
                    del self.saved_artifacts[md5_]
            else:
                #print "Saving Artifact to SA"
                self.saved_artifacts[md5_] = (properties, data)

    def process_saved_artifacts(self):
        """
        Process anything in saved_artifacts that didn't have a match.
        """

        for md5_, value in self.saved_artifacts.iteritems():
            (saved_obj, data) = value
            if saved_obj._XSI_TYPE == 'FileObjectType':
                #print "Only File found in SA"
                sample = Sample.from_cybox(saved_obj, [self.source])
                db_sample = Sample.objects(md5=md5_).first()
                if db_sample:
                    # flat out replacing cybox sample object with one from db.
                    # we add the source to track we got a copy from TAXII.
                    # if we have a metadata only doc, the add_file_data below
                    # will generate metadata for us.
                    sample = db_sample
                    sample.add_source(self.source)
                if data:
                    sample.add_file_data(data)
                sample.save(username=self.source_instance.analyst)
                self.samples.append(('Sample', sample.md5))
            # currently not adding random artifacts with no metadata
            #elif saved_obj._XSI_TYPE == 'ArtifactObjectType':
            #    print "Found matching Artifact in SA"

    def relate_objects(self):
        """
        for now we are relating all objects to the event with a common
        relationship type that is most likely inaccurate. Need to get actual
        relationship out of the cybox document once we are storing it there.
        """

        for (type_, event_id) in self.events:
            event_obj = class_from_value(type_, event_id)
            finished_objects = [event_obj]
            for (t, v) in self.samples + self.emails + self.indicators:
                obj = class_from_value(t, v)
                obj.add_relationship(event_obj,
                                     rel_type="Related_To",
                                     analyst=self.source_instance.analyst)
                finished_objects.append(obj)

            for f in finished_objects:
                f.save(username=self.source_instance.analyst)

        # If we have no event relate every object to every other object.
        if not self.events:
            finished_objects = []
            for (t, v) in self.samples + self.emails + self.indicators:
                obj = class_from_value(t, v)
                # Prime the list...
                if not finished_objects:
                    finished_objects.append(obj)
                    continue

                for right in finished_objects:
                    obj.add_relationship(right,
                                         rel_type="Related_To",
                                         analyst=self.source_instance.analyst)
                finished_objects.append(obj)

            for f in finished_objects:
                f.save(username=self.source_instance.analyst)
