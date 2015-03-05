import datetime, base64

from StringIO import StringIO

from crits.actors.actor import Actor
from crits.actors.handlers import add_new_actor, update_actor_tags
from crits.certificates.handlers import handle_cert_file
from crits.domains.handlers import upsert_domain, get_domain
from crits.emails.handlers import handle_email_fields
from crits.events.handlers import add_new_event
from crits.indicators.indicator import Indicator
from crits.indicators.handlers import handle_indicator_ind
from crits.ips.handlers import ip_add_update
from crits.objects.object_mapper import make_crits_object
from crits.pcaps.handlers import handle_pcap_file
from crits.raw_data.handlers import handle_raw_data_file
from crits.samples.handlers import handle_file
from crits.core.crits_mongoengine import EmbeddedSource
from crits.core.handlers import does_source_exist

from cybox.objects.artifact_object import Artifact
from cybox.objects.address_object import Address
from cybox.objects.domain_name_object import DomainName
from cybox.objects.email_message_object import EmailMessage
from cybox.objects.file_object import File

from stix.common import StructuredText
from stix.core import STIXPackage, STIXHeader

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
            raise STIXParserException("No source to attribute data to.")

        self.source_instance.reference = reference
        self.source.instances.append(self.source_instance)

        if make_event:
            title = "STIX Document %s" % self.package.id_
            event_type = "Collective Threat Intelligence"
            date = datetime.datetime.now()
            description = str(date)
            header = self.package.stix_header
            if isinstance(header, STIXHeader):
                if header.title:
                    title = header.title
                if hasattr(header, 'package_intents'):
                    event_type = str(header.package_intents[0])
                description = header.description
                if isinstance(description, StructuredText):
                    try:
                        description = description.to_dict()
                    except:
                        pass
            res = add_new_event(title,
                                description,
                                event_type,
                                self.source.name,
                                self.source_instance.method,
                                self.source_instance.reference,
                                date,
                                self.source_instance.analyst)
            if res['success']:
                self.imported.append(('Event',
                                      res['object']))
            else:
                self.failed.append((res['message'],
                                    "STIX Event",
                                    ""))

        if self.package.indicators:
            self.parse_indicators(self.package.indicators)

        if self.package.observables and self.package.observables.observables:
            self.parse_observables(self.package.observables.observables)

        if self.package.threat_actors:
            self.parse_threat_actors(self.package.threat_actors)

    def parse_threat_actors(self, threat_actors):
        """
        Parse list of Threat Actors.

        :param threat_actors: List of STIX ThreatActors.
        :type threat_actors: List of STIX ThreatActors.
        """
        from stix.threat_actor import ThreatActor
        analyst = self.source_instance.analyst
        for threat_actor in threat_actors: # for each STIX ThreatActor
            try: # create CRITs Actor from ThreatActor
                if isinstance(threat_actor, ThreatActor):
                    name = str(threat_actor.title)
                    description = str(threat_actor.description)
                    res = add_new_actor(name=name,
                                        description=description,
                                        source=[self.source],
                                        analyst=analyst)
                    if res['success']:
                        sl = ml = tl = il = []
                        for s in threat_actor.sophistications:
                            sl.append(str(s.value))
                        update_actor_tags(res['id'],
                                            'ActorSophistication',
                                            sl,
                                            analyst)
                        for m in threat_actor.motivations:
                            ml.append(str(m.value))
                        update_actor_tags(res['id'],
                                            'ActorMotivation',
                                            ml,
                                            analyst)
                        for t in threat_actor.types:
                            tl.append(str(t.value))
                        update_actor_tags(res['id'],
                                            'ActorThreatType',
                                            tl,
                                            analyst)
                        for i in threat_actor.intended_effects:
                            il.append(str(i.value))
                        update_actor_tags(res['id'],
                                            'ActorIntendedEffect',
                                            il,
                                            analyst)
                        obj = Actor.objects(id=res['id']).first()
                        self.imported.append((Actor._meta['crits_type'], obj))
                    else:
                        self.failed.append((res['message'],
                                            type(threat_actor).__name__,
                                            "")) # note for display in UI
            except Exception, e:
                self.failed.append((e.message, type(threat_actor).__name__,
                                    "")) # note for display in UI

    def parse_indicators(self, indicators):
        """
        Parse list of indicators.

        :param indicators: List of STIX indicators.
        :type indicators: List of STIX indicators.
        """

        analyst = self.source_instance.analyst
        for indicator in indicators: # for each STIX indicator
            for observable in indicator.observables: # get each observable from indicator (expecting only 1)
                try: # create CRITs Indicator from observable
                    item = observable.object_.properties
                    obj = make_crits_object(item)
                    if obj.name and obj.name != obj.object_type:
                        ind_type = "%s - %s" % (obj.object_type, obj.name)
                    else:
                        ind_type = obj.object_type
                    res = handle_indicator_ind(obj.value,
                                               self.source,
                                               None,
                                               ind_type,
                                               analyst,
                                               add_domain=True,
                                               add_relationship=True)
                    if res['success']:
                        self.imported.append((Indicator._meta['crits_type'],
                                              res['object']))
                    else:
                        self.failed.append((res['message'],
                                            type(item).__name__,
                                            item.parent.id_)) # note for display in UI
                except Exception, e: # probably caused by cybox object we don't handle
                    self.failed.append((e.message, type(item).__name__, item.parent.id_)) # note for display in UI

    def parse_observables(self, observables):
        """
        Parse list of observables in STIX doc.

        :param observables: List of STIX observables.
        :type observables: List of STIX observables.
        """

        analyst = self.source_instance.analyst
        for obs in observables: # for each STIX observable
            if not obs.object_ or not obs.object_.properties:
                self.failed.append(("No valid object_properties was found!",
                                    type(obs).__name__,
                                    obs.id_)) # note for display in UI
                continue
            try: # try to create CRITs object from observable
                item = obs.object_.properties
                if isinstance(item, Address):
                    imp_type = "IP"
                    ip = str(item.address_value)
                    iptype = "Address - %s" % item.category
                    res = ip_add_update(ip,
                                        iptype,
                                        [self.source],
                                        analyst=analyst,
                                        is_add_indicator=True)
                elif isinstance(item, DomainName):
                    imp_type = "Domain"
                    (sdomain, domain) = get_domain(str(item.value))
                    res = upsert_domain(sdomain,
                                        domain,
                                        [self.source],
                                        username=analyst)
                elif isinstance(item, Artifact):
                    # Not sure if this is right, and I believe these can be
                    # encoded in a couple different ways.
                    imp_type = "RawData"
                    rawdata = base64.b64decode(item.data)
                    description = str(item.description)
                    # TODO: find out proper ways to determine title, datatype,
                    #       tool_name, tool_version
                    title = "Artifact for Event: STIX Document %s" % self.package.id_
                    res = handle_raw_data_file(rawdata,
                                               self.source.name,
                                               user=analyst,
                                               description=description,
                                               title=title,
                                               data_type="Text",
                                               tool_name="TAXII",
                                               tool_version=None,
                                               method=self.source_instance.method,
                                               reference=self.source_instance.reference)
                elif (isinstance(item, File) and
                      item.custom_properties and
                      item.custom_properties[0].name == "crits_type" and
                      item.custom_properties[0]._value == "Certificate"):
                    imp_type = "Certificate"
                    description = str(item.description)
                    filename = str(item.file_name)
                    data = None
                    for obj in item.parent.related_objects:
                        if isinstance(obj.properties, Artifact):
                            data = base64.b64decode(obj.properties.data)
                    res = handle_cert_file(filename,
                                           data,
                                           self.source,
                                           user=analyst,
                                           description=description)
                elif isinstance(item, File) and self.has_network_artifact(item):
                    imp_type = "PCAP"
                    description = str(item.description)
                    filename = str(item.file_name)
                    data = None
                    for obj in item.parent.related_objects:
                        if (isinstance(obj.properties, Artifact) and
                            obj.properties.type_ == Artifact.TYPE_NETWORK):
                            data = base64.b64decode(obj.properties.data)
                    res = handle_pcap_file(filename,
                                           data,
                                           self.source,
                                           user=analyst,
                                           description=description)
                elif isinstance(item, File):
                    imp_type = "Sample"
                    filename = str(item.file_name)
                    md5 = item.md5
                    data = None
                    for obj in item.parent.related_objects:
                        if (isinstance(obj.properties, Artifact) and
                            obj.properties.type_ == Artifact.TYPE_FILE):
                            data = base64.b64decode(obj.properties.data)
                    res = handle_file(filename,
                                      data,
                                      self.source,
                                      user=analyst,
                                      md5_digest=md5,
                                      is_return_only_md5=False)
                elif isinstance(item, EmailMessage):
                    imp_type = "Email"
                    data = {}
                    data['source'] = self.source.name
                    data['source_method'] = self.source_instance.method
                    data['source_reference'] = self.source_instance.reference
                    data['message_id'] = str(item.header.message_id)
                    data['subject'] = str(item.header.subject)
                    data['sender'] = str(item.header.sender)
                    data['reply_to'] = str(item.header.reply_to)
                    data['x_originating_ip'] = str(item.header.x_originating_ip)
                    data['x_mailer'] = str(item.header.x_mailer)
                    data['boundary'] = str(item.header.boundary)
                    data['raw_body'] = str(item.raw_body)
                    data['raw_header'] = str(item.raw_header)
                    data['helo'] = str(item.email_server)
                    data['from_address'] = str(item.header.from_)
                    data['date'] = item.header.date
                    data['to'] = [str(r) for r in item.header.to.to_list()]
                    res = handle_email_fields(data,
                                              analyst,
                                              "TAXII")
                else: # try to parse all other possibilities as Indicator
                    imp_type = "Indicator"
                    obj = make_crits_object(item)
                    if obj.name and obj.name != obj.object_type:
                        ind_type = "%s - %s" % (obj.object_type, obj.name)
                    else:
                        ind_type = obj.object_type
                    res = handle_indicator_ind(obj.value,
                                               self.source,
                                               None,
                                               ind_type,
                                               analyst,
                                               add_domain=True,
                                               add_relationship=True)
                if res['success']:
                    self.imported.append((imp_type,
                                          res['object'])) # use class to parse object
                else:
                    if 'reason' in res:
                        msg = res['reason']
                    elif 'message' in res:
                        msg = res['message']
                    else:
                        msg = "Failed for unknown reason."
                    self.failed.append((msg,
                                        type(obs).__name__,
                                        obs.id_)) # note for display in UI
            except Exception, e: # probably caused by cybox object we don't handle
                self.failed.append((e.message,
                                    type(item).__name__,
                                    item.parent.id_)) # note for display in UI

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


