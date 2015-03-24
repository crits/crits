from bson.objectid import ObjectId

def class_from_id(type_, _id):
    """
    Return an instantiated class object.

    :param type_: The CRITs top-level object type.
    :type type_: str
    :param _id: The ObjectId to search for.
    :type _id: str
    :returns: class which inherits from
              :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    """

    # doing this to avoid circular imports
    from crits.actors.actor import ActorThreatType, ActorMotivation
    from crits.actors.actor import ActorSophistication, ActorIntendedEffect
    from crits.actors.actor import ActorThreatIdentifier, Actor
    from crits.campaigns.campaign import Campaign
    from crits.certificates.certificate import Certificate
    from crits.comments.comment import Comment
    from crits.core.crits_mongoengine import RelationshipType
    from crits.core.source_access import SourceAccess
    from crits.core.user_role import UserRole
    from crits.domains.domain import Domain
    from crits.emails.email import Email
    from crits.events.event import Event, EventType
    from crits.indicators.indicator import Indicator, IndicatorAction
    from crits.ips.ip import IP
    from crits.objects.object_type import ObjectType
    from crits.pcaps.pcap import PCAP
    from crits.raw_data.raw_data import RawData, RawDataType
    from crits.samples.backdoor import Backdoor
    from crits.samples.exploit import Exploit
    from crits.samples.sample import Sample
    from crits.screenshots.screenshot import Screenshot
    from crits.targets.target import Target

    if not _id:
        return None

    # make sure it's a string
    _id = str(_id)

    # Use bson.ObjectId to make sure this is a valid ObjectId, otherwise
    # the queries below will raise a ValidationError exception.
    if not ObjectId.is_valid(_id.decode('utf8')):
        return None

    if type_ == 'Actor':
        return Actor.objects(id=_id).first()
    elif type_ == 'ActorThreatIdentifier':
        return ActorThreatIdentifier.objects(id=_id).first()
    elif type_ == 'ActorThreatType':
        return ActorThreatType.objects(id=_id).first()
    elif type_ == 'ActorMotivation':
        return ActorMotivation.objects(id=_id).first()
    elif type_ == 'ActorSophistication':
        return ActorSophistication.objects(id=_id).first()
    elif type_ == 'ActorIntendedEffect':
        return ActorIntendedEffect.objects(id=_id).first()
    elif type_ == 'Backdoor':
        return Backdoor.objects(id=_id).first()
    elif type_ == 'Campaign':
        return Campaign.objects(id=_id).first()
    elif type_ == 'Certificate':
        return Certificate.objects(id=_id).first()
    elif type_ == 'Comment':
        return Comment.objects(id=_id).first()
    elif type_ == 'Domain':
        return Domain.objects(id=_id).first()
    elif type_ == 'Email':
        return Email.objects(id=_id).first()
    elif type_ == 'Event':
        return Event.objects(id=_id).first()
    elif type_ == 'EventType':
        return EventType.objects(id=_id).first()
    elif type_ == 'Exploit':
        return Exploit.objects(id=_id).first()
    elif type_ == 'Indicator':
        return Indicator.objects(id=_id).first()
    elif type_ == 'IndicatorAction':
        return IndicatorAction.objects(id=_id).first()
    elif type_ == 'IP':
        return IP.objects(id=_id).first()
    elif type_ == 'ObjectType':
        return ObjectType.objects(id=_id).first()
    elif type_ == 'PCAP':
        return PCAP.objects(id=_id).first()
    elif type_ == 'RawData':
        return RawData.objects(id=_id).first()
    elif type_ == 'RawDataType':
        return RawDataType.objects(id=_id).first()
    elif type_ == 'RelationshipType':
        return RelationshipType.objects(id=_id).first()
    elif type_ == 'Sample':
        return Sample.objects(id=_id).first()
    elif type_ == 'SourceAccess':
        return SourceAccess.objects(id=_id).first()
    elif type_ == 'Screenshot':
        return Screenshot.objects(id=_id).first()
    elif type_ == 'Target':
        return Target.objects(id=_id).first()
    elif type_ == 'UserRole':
        return UserRole.objects(id=_id).first()
    else:
        return None

def class_from_value(type_, value):
    """
    Return an instantiated class object.

    :param type_: The CRITs top-level object type.
    :type type_: str
    :param value: The value to search for.
    :type value: str
    :returns: class which inherits from
              :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    """

    # doing this to avoid circular imports
    from crits.actors.actor import ActorThreatType, ActorMotivation
    from crits.actors.actor import ActorSophistication, ActorIntendedEffect
    from crits.actors.actor import ActorThreatIdentifier, Actor
    from crits.campaigns.campaign import Campaign
    from crits.certificates.certificate import Certificate
    from crits.comments.comment import Comment
    from crits.domains.domain import Domain
    from crits.emails.email import Email
    from crits.events.event import Event
    from crits.indicators.indicator import Indicator
    from crits.ips.ip import IP
    from crits.pcaps.pcap import PCAP
    from crits.raw_data.raw_data import RawData
    from crits.samples.sample import Sample
    from crits.screenshots.screenshot import Screenshot
    from crits.targets.target import Target

    # Make sure value is a string...
    value = str(value)

    # Use bson.ObjectId to make sure this is a valid ObjectId, otherwise
    # the queries below will raise a ValidationError exception.
    if (type_ in ['Comment', 'Email', 'Event', 'Indicator', 'Screenshot'] and
       not ObjectId.is_valid(value.decode('utf8'))):
        return None

    if type_ == 'Actor':
        return Actor.objects(name=value).first()
    elif type_ == 'ActorThreatIdentifier':
        return ActorThreatIdentifier.objects(name=value).first()
    elif type_ == 'ActorThreatType':
        return ActorThreatType.objects(name=value).first()
    elif type_ == 'ActorMotivation':
        return ActorMotivation.objects(name=value).first()
    elif type_ == 'ActorSophistication':
        return ActorSophistication.objects(name=value).first()
    elif type_ == 'ActorIntendedEffect':
        return ActorIntendedEffect.objects(name=value).first()
    elif type_ == 'Campaign':
        return Campaign.objects(name=value).first()
    elif type_ == 'Certificate':
        return Certificate.objects(md5=value).first()
    elif type_ == 'Comment':
        return Comment.objects(id=value).first()
    elif type_ == 'Domain':
        return Domain.objects(domain=value).first()
    elif type_ == 'Email':
        return Email.objects(id=value).first()
    elif type_ == 'Event':
        return Event.objects(id=value).first()
    elif type_ == 'Indicator':
        return Indicator.objects(id=value).first()
    elif type_ == 'IP':
        return IP.objects(ip=value).first()
    elif type_ == 'PCAP':
        return PCAP.objects(md5=value).first()
    elif type_ == 'RawData':
        return RawData.objects(md5=value).first()
    elif type_ == 'Sample':
        return Sample.objects(md5=value).first()
    elif type_ == 'Screenshot':
        return Screenshot.objects(id=value).first()
    elif type_ == 'Target':
        return Target.objects(email_address__iexact=value).first()
    else:
        return None

def class_from_type(type_):
    """
    Return a class object.

    :param type_: The CRITs top-level object type.
    :type type_: str
    :returns: class which inherits from
              :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    """

    # doing this to avoid circular imports
    from crits.actors.actor import ActorThreatType, ActorMotivation
    from crits.actors.actor import ActorSophistication, ActorIntendedEffect
    from crits.actors.actor import ActorThreatIdentifier, Actor
    from crits.campaigns.campaign import Campaign
    from crits.certificates.certificate import Certificate
    from crits.comments.comment import Comment
    from crits.core.crits_mongoengine import RelationshipType
    from crits.core.source_access import SourceAccess
    from crits.core.user_role import UserRole
    from crits.domains.domain import Domain
    from crits.emails.email import Email
    from crits.events.event import Event, EventType
    from crits.indicators.indicator import Indicator, IndicatorAction
    from crits.ips.ip import IP
    from crits.objects.object_type import ObjectType
    from crits.pcaps.pcap import PCAP
    from crits.raw_data.raw_data import RawData, RawDataType
    from crits.samples.backdoor import Backdoor
    from crits.samples.exploit import Exploit
    from crits.samples.sample import Sample
    from crits.screenshots.screenshot import Screenshot
    from crits.targets.target import Target

    if type_ == 'Actor':
        return Actor
    elif type_ == 'ActorThreatIdentifier':
        return ActorThreatIdentifier
    elif type_ == 'ActorThreatType':
        return ActorThreatType
    elif type_ == 'ActorMotivation':
        return ActorMotivation
    elif type_ == 'ActorSophistication':
        return ActorSophistication
    elif type_ == 'ActorIntendedEffect':
        return ActorIntendedEffect
    elif type_ == 'Backdoor':
        return Backdoor
    elif type_ == 'Campaign':
        return Campaign
    elif type_ == 'Certificate':
        return Certificate
    elif type_ == 'Comment':
        return Comment
    elif type_ == 'Domain':
        return Domain
    elif type_ == 'Email':
        return Email
    elif type_ == 'Event':
        return Event
    elif type_ == 'EventType':
        return EventType
    elif type_ == 'Exploit':
        return Exploit
    elif type_ == 'Indicator':
        return Indicator
    elif type_ == 'IndicatorAction':
        return IndicatorAction
    elif type_ == 'IP':
        return IP
    elif type_ == 'ObjectType':
        return ObjectType
    elif type_ == 'PCAP':
        return PCAP
    elif type_ == 'RawData':
        return RawData
    elif type_ == 'RawDataType':
        return RawDataType
    elif type_ == 'RelationshipType':
        return RelationshipType
    elif type_ == 'Sample':
        return Sample
    elif type_ == 'SourceAccess':
        return SourceAccess
    elif type_ == 'Screenshot':
        return Screenshot
    elif type_ == 'Target':
        return Target
    elif type_ == 'UserRole':
        return UserRole
    else:
        return None
