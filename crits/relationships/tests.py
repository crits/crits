from django.test import SimpleTestCase

from crits.relationships.handlers import forge_relationship, update_relationship_reasons, update_relationship_confidences
import crits.core.handlers as core_handlers
from crits.core.user import CRITsUser
from crits.core.source_access import SourceAccess
from crits.core.class_mapper import class_from_type
from crits.campaigns.campaign import Campaign
from crits.vocabulary.relationships import RelationshipTypes
from django.conf import settings

from crits.actors.actor import Actor
from crits.backdoors.backdoor import Backdoor
from crits.certificates.certificate import Certificate
from crits.domains.domain import Domain
from crits.emails.email import Email
from crits.events.event import Event
from crits.vocabulary.events import EventTypes
from crits.exploits.exploit import Exploit
from crits.indicators.indicator import Indicator
from crits.ips.ip import IP
from crits.pcaps.pcap import PCAP
from crits.raw_data.raw_data import RawData
from crits.samples.sample import Sample
from crits.signatures.signature import Signature
from crits.targets.target import Target

TUSER_NAME = "test_user"
TUSER_PASS = "!@#j54kfeimn?>S<D"
TUSER_EMAIL = "test_user@example.com"
TUSER2_NAME = "second_testUser"
TUSER2_PASS = "!@#saasdfasfwefwe?>S<Dd"
TUSER2_EMAIL = "asdfsaser@example.com"
TCAMPAIGN1 = "Test_Campain1"
TCAMPAIGN2 = "Test_Campain2"
TSRC = "TestSource12345"
TRELATIONSHIP_TYPE = RelationshipTypes.CREATED
TRELATIONSHIP_INV_TYPE = RelationshipTypes.CREATED_BY
TRELATIONSHIP2_TYPE = RelationshipTypes.REGISTERED
TRELATIONSHIP2_INV_TYPE = RelationshipTypes.REGISTERED_TO
TRELATIONSHIP_CONFIDENCE = 'high'
TRELATIONSHIP_NEW_CONFIDENCE = 'medium'
TRELATIONSHIP_NEW_REASON = "Because I Said So"

TACTOR = "Actor12345"
TBACKDOOR = "Backdoor12345"
TCAMPAIGN3 = "Test_Campain3"
TCERT_FNAME = "TestFile12345"
TCERT_FTYPE = "TestFileType12345"
TDOMAIN = "testdomain12345.com"
TEMAIL_REPLYTO = "testrecip12345@gmail123.com"
TEVENT_TITLE = "TestEvent12345"
TEVENT_TYPE = EventTypes.values()[0]
TEVENT_DESC = "TestDescription12345"
TEXPLOIT = "TestExploit12345"
TINDICATOR = "TestIndicator12345"
TINDICATOR_TYPE = "API Key"
TIP = "200.199.198.197"
TPCAP = "TestPCAP12345.pcap"
TRAWDATA_TITLE = "TestRawData12345"
TSAMPLE_FNAME = "TestFileName12345"
TSAMPLE_MD5 = "11111111111111111111111111111111"
TSIGNATURE_TITLE = "TestSample12345"
TTARGET = "testtarget12345@gmail123.com"

def prep_db():
    """
    Prep database for test.
    """
    clean_db()
    # Add User
    user = CRITsUser.create_user(
                          username=TUSER_NAME,
                          password=TUSER_PASS,
                          email=TUSER_EMAIL,
                          )
    user.sources = [TSRC]
    user.save()
    user2 = CRITsUser.create_user(
                          username=TUSER2_NAME,
                          password=TUSER2_PASS,
                          email=TUSER2_EMAIL,
                          )
    user2.sources = [TSRC]
    user2.save()
    
    core_handlers.add_new_source(TSRC, user)

    campaign1 = Campaign(name=TCAMPAIGN1)
    campaign1.save(username=user.username)
    campaign2 = Campaign(name=TCAMPAIGN2)
    campaign2.save(username=user.username)

    # Migration Testing
    actor1 = Actor(name=TACTOR)
    actor1.add_source(source=TSRC,analyst=user.username)
    actor1.save(username=user.username)
    
    backdoor1 = Backdoor(name=TBACKDOOR)
    backdoor1.add_source(source=TSRC,analyst=user.username)
    backdoor1.save(username=user.username)
    
    campaign3 = Campaign(name=TCAMPAIGN3)
    campaign3.save(username=user.username)
    
    certificate1 = Certificate(filename=TCERT_FNAME,filetype=TCERT_FTYPE)
    certificate1.add_source(source=TSRC,analyst=user.username)
    certificate1.save(username=user.username) 

    domain1 = Domain(domain=TDOMAIN)
    domain1.add_source(source=TSRC,analyst=user.username)
    domain1.save(username=user.username) 

    email1 = Email(reply_to=TEMAIL_REPLYTO)
    email1.add_source(source=TSRC,analyst=user.username)
    email1.save(username=user.username) 

    event1 = Event(title=TEVENT_TITLE,event_type=TEVENT_TYPE,description=TEVENT_DESC)
    event1.add_source(source=TSRC,analyst=user.username)
    event1.save(username=user.username)
    
    exploit1 = Exploit(name=TEXPLOIT)
    exploit1.add_source(source=TSRC,analyst=user.username)
    exploit1.save(username=user.username)

    indicator1 = Indicator(value=TINDICATOR,ind_type=TINDICATOR_TYPE)
    indicator1.add_source(source=TSRC,analyst=user.username)
    indicator1.save(username=user.username)

    ip1 = IP(ip=TIP)
    ip1.add_source(source=TSRC,analyst=user.username)
    ip1.save(username=user.username)

    pcap1 = PCAP(filename=TPCAP)
    pcap1.add_source(source=TSRC,analyst=user.username)
    pcap1.save(username=user.username)
    
    rawdata1 = RawData(title=TRAWDATA_TITLE)
    rawdata1.add_source(source=TSRC,analyst=user.username)
    rawdata1.save(username=user.username)
    
    sample1 = Sample(filename=TSAMPLE_FNAME,md5=TSAMPLE_MD5)
    sample1.add_source(source=TSRC,analyst=user.username)
    sample1.save(username=user.username)
    
    signature1 = Signature(title=TSIGNATURE_TITLE)
    signature1.add_source(source=TSRC,analyst=user.username)
    signature1.save(username=user.username)
    
    target1 = Target(email_address=TTARGET)
    target1.save(username=user.username)
    
def clean_db():
    """
    Clean database for test.
    """
    user = CRITsUser.objects(username=TUSER_NAME).first()
    if user:
        user.delete()
    user2 = CRITsUser.objects(username=TUSER2_NAME).first()
    if user2:
        user2.delete()
    campaign1 = Campaign.objects(name=TCAMPAIGN1).first()
    if campaign1:
        campaign1.delete()
    campaign2 = Campaign.objects(name=TCAMPAIGN2).first()
    if campaign2:
        campaign2.delete()

    actor1 = Actor.objects(name=TACTOR).first()
    if actor1:
        actor1.delete()
    backdoor1 = Backdoor.objects(name=TBACKDOOR).first()
    if backdoor1:
        backdoor1.delete()
    campaign3 = Campaign.objects(name=TCAMPAIGN3).first()
    if campaign3:
        campaign3.delete()
    certificate1 = Certificate.objects(filename=TCERT_FNAME,filetype=TCERT_FTYPE).first()
    if certificate1:
        certificate1.delete()
    domain1 = Domain.objects(domain=TDOMAIN).first()
    if domain1:
        domain1.delete()
    email1 = Email.objects(reply_to=TEMAIL_REPLYTO).first()
    if email1:
        email1.delete()

    event1 = Event.objects(title=TEVENT_TITLE,event_type=TEVENT_TYPE).first()
    if event1:
        event1.delete()

    exploit1 = Exploit.objects(name=TEXPLOIT).first()
    if exploit1:
        exploit1.delete()

    indicator1 = Indicator.objects(value=TINDICATOR,ind_type=TINDICATOR_TYPE).first()
    if indicator1:
        indicator1.delete()

    ip1 = IP.objects(ip=TIP).first()
    if ip1:
        ip1.delete()
    
    pcap1 = PCAP.objects(filename=TPCAP).first()
    if pcap1:
        pcap1.delete()

    rawdata1 = RawData.objects(title=TRAWDATA_TITLE).first()
    if rawdata1:
        rawdata1.delete()
    
    sample1 = Sample.objects(filename=TSAMPLE_FNAME,md5=TSAMPLE_MD5).first()
    if sample1:
        sample1.delete()
    
    signature1 = Signature.objects(title=TSIGNATURE_TITLE).first()
    if signature1:
        signature1.delete()
        
    target1 = Target.objects(email_address=TTARGET).first()
    if target1:
        target1.delete()

    source1 = SourceAccess.objects(name=TSRC).first()
    if source1:
        source1.delete()
class RelationshipConfidenceAndReasonTests(SimpleTestCase):
    """
    Test Domain Handlers
    """
    def setUp(self):
        prep_db()
        self.user = CRITsUser.objects(username=TUSER_NAME).first()
        self.user2 = CRITsUser.objects(username=TUSER2_NAME).first()
        self.campaign1 = Campaign.objects(name=TCAMPAIGN1).first()
        self.campaign2 = Campaign.objects(name=TCAMPAIGN2).first()
        forge_relationship(class_=self.campaign1,
                           right_class=self.campaign2,
                           rel_type=TRELATIONSHIP_TYPE,
                           user=self.user.username,
                           rel_confidence=TRELATIONSHIP_CONFIDENCE)
        # This relationship should not get forged, as it is identical to above relationship.
        forge_relationship(class_=self.campaign2,
                           right_class=self.campaign1,
                           rel_type=TRELATIONSHIP_INV_TYPE,
                           user=self.user.username,
                           rel_confidence=TRELATIONSHIP_CONFIDENCE)
        self.relationship1 = self.campaign1.get_relationships(sorted=False,meta=False)[0]
        self.relationship2 = self.campaign2.get_relationships(sorted=False,meta=False)[0]
        
        # Test for all TLOs
        self.tlo_tests = [Actor.objects(name=TACTOR).first(),
                          Backdoor.objects(name=TBACKDOOR).first(),
                          Campaign.objects(name=TCAMPAIGN3).first(),
                          Certificate.objects(filename=TCERT_FNAME,filetype=TCERT_FTYPE).first(),
                          Domain.objects(domain=TDOMAIN).first(),
                          Email.objects(reply_to=TEMAIL_REPLYTO).first(),
                          Event.objects(title=TEVENT_TITLE,event_type=TEVENT_TYPE).first(),
                          Exploit.objects(name=TEXPLOIT).first(),
                          Indicator.objects(value=TINDICATOR,ind_type=TINDICATOR_TYPE).first(),
                          IP.objects(ip=TIP).first(),
                          PCAP.objects(filename=TPCAP).first(),
                          RawData.objects(title=TRAWDATA_TITLE).first(),
                          Sample.objects(filename=TSAMPLE_FNAME,md5=TSAMPLE_MD5).first(),
                          Signature.objects(title=TSIGNATURE_TITLE).first(),
                          Target.objects(email_address=TTARGET).first()]
        for counter,tlo in enumerate(self.tlo_tests):
            if counter == 0:
                left_class = self.tlo_tests[-1]
            else:
                left_class = self.tlo_tests[counter-1]
            right_class = tlo
            forge_relationship(class_=left_class,
                               right_class=right_class,
                               rel_type=TRELATIONSHIP_TYPE,
                               user=self.user.username,
                               rel_confidence=TRELATIONSHIP_CONFIDENCE)
            forge_relationship(class_=right_class,
                               right_class=left_class,
                               rel_type=TRELATIONSHIP2_TYPE,
                               user=self.user.username,
                               rel_confidence=TRELATIONSHIP_CONFIDENCE)

    def tearDown(self):
        clean_db()
    def testDuplicateRelationship(self):
        if (len(self.campaign1.get_relationships(sorted=False,meta=False)) > 1 or 
            len(self.campaign2.get_relationships(sorted=False,meta=False)) > 1):
            raise Exception("Duplicate relationships forged.")
    def testCreateRelationship(self):
        self.assertEqual(self.relationship1['rel_confidence'], TRELATIONSHIP_CONFIDENCE)
        self.assertEqual(self.relationship2['rel_confidence'], TRELATIONSHIP_CONFIDENCE)
        self.assertEqual(self.relationship1['analyst'], self.user.username)
        self.assertEqual(self.relationship2['analyst'], self.user.username)
        self.assertEqual(self.relationship1['other_obj']['rel_type'], TRELATIONSHIP_TYPE)
        self.assertEqual(self.relationship2['other_obj']['rel_type'], TRELATIONSHIP_INV_TYPE)
    def testChangingReason(self):
        self.assertEqual(self.relationship1['rel_reason'], "")
        self.assertEqual(self.relationship2['rel_reason'], "")
        update_relationship_reasons(left_class=self.campaign1,
                                    right_class=self.campaign2,
                                    rel_type=TRELATIONSHIP_TYPE,
                                    analyst=self.user2.username,
                                    new_reason=TRELATIONSHIP_NEW_REASON)
        campaign1 = Campaign.objects.get(id=self.campaign1.id)
        campaign2 = Campaign.objects.get(id=self.campaign2.id)
        self.relationship1 = self.campaign1.get_relationships(sorted=False,meta=False)[0]
        self.relationship2 = self.campaign2.get_relationships(sorted=False,meta=False)[0]
        self.assertEqual(self.relationship1['rel_reason'], TRELATIONSHIP_NEW_REASON)
        self.assertEqual(self.relationship2['rel_reason'], TRELATIONSHIP_NEW_REASON)
    def testChangingConfidence(self):
        self.assertEqual(self.relationship1['rel_confidence'], TRELATIONSHIP_CONFIDENCE)
        self.assertEqual(self.relationship2['rel_confidence'], TRELATIONSHIP_CONFIDENCE)
        update_relationship_confidences(left_class=self.campaign1,
                                    right_class=self.campaign2,
                                    rel_type=TRELATIONSHIP_TYPE,
                                    analyst=self.user2.username,
                                    new_confidence=TRELATIONSHIP_NEW_CONFIDENCE)
        self.relationship1 = self.campaign1.get_relationships(sorted=False,meta=False)[0]
        self.relationship2 = self.campaign2.get_relationships(sorted=False,meta=False)[0]
        self.assertEqual(self.relationship1['rel_confidence'], TRELATIONSHIP_NEW_CONFIDENCE)
        self.assertEqual(self.relationship2['rel_confidence'], TRELATIONSHIP_NEW_CONFIDENCE)
    def testAllTLOs(self):
        for counter,tlo in enumerate(self.tlo_tests):
            if counter == 0:
                left_class = self.tlo_tests[-1]
            else:
                left_class = self.tlo_tests[counter-1]
            right_class = tlo
            left_relationships = left_class.get_relationships(sorted=False,meta=False)
            right_relationships = right_class.get_relationships(sorted=False,meta=False)
            if len(left_relationships) != 4 or len(right_relationships) != 4:
                raise Exception("Unexpected number of relationships.  Expecting 4 per TLO.")
            found1 = False
            found2 = False
            found3 = False
            found4 = False
            for rel in left_relationships:
                if (rel['other_obj']['obj_id'] == right_class.id and
                    rel['other_obj']['obj_type'] ==  right_class._meta['crits_type'] and
                    rel['other_obj']['rel_type'] == TRELATIONSHIP_TYPE):
                    found1 = True
                if (rel['other_obj']['obj_id'] == right_class.id and
                    rel['other_obj']['obj_type'] ==  right_class._meta['crits_type'] and
                    rel['other_obj']['rel_type'] == TRELATIONSHIP2_INV_TYPE):
                    found2 = True
            for rel in right_relationships:
                if (rel['other_obj']['obj_id'] == left_class.id and
                    rel['other_obj']['obj_type'] ==  left_class._meta['crits_type'] and
                    rel['other_obj']['rel_type'] == TRELATIONSHIP_INV_TYPE):
                    found3 = True
                if (rel['other_obj']['obj_id'] == left_class.id and
                    rel['other_obj']['obj_type'] ==  left_class._meta['crits_type'] and
                    rel['other_obj']['rel_type'] == TRELATIONSHIP2_TYPE):
                    found4 = True
            if not (found1 and found2 and found3 and found4):
                raise Exception("Not all relationships forged.")