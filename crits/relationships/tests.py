from django.test import SimpleTestCase

from crits.relationships.handlers import forge_relationship, update_relationship_reasons, update_relationship_confidences
from crits.core.user import CRITsUser
from crits.campaigns.campaign import Campaign
from crits.vocabulary.relationships import RelationshipTypes

TUSER_NAME = "test_user"
TUSER_PASS = "!@#j54kfeimn?>S<D"
TUSER_EMAIL = "test_user@example.com"
TUSER2_NAME = "second_testUser"
TUSER2_PASS = "!@#saasdfasfwefwe?>S<Dd"
TUSER2_EMAIL = "asdfsaser@example.com"
TCAMPAIGN1 = "Test_Campain1"
TCAMPAIGN2 = "Test_Campain2"
TRELATIONSHIP_TYPE = RelationshipTypes.RELATED_TO
TRELATIONSHIP_CONFIDENCE = 'high'
TRELATIONSHIP_NEW_CONFIDENCE = 'medium'
TRELATIONSHIP_NEW_REASON = "Because I Said So"

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
    user.save()
    user2 = CRITsUser.create_user(
                          username=TUSER2_NAME,
                          password=TUSER2_PASS,
                          email=TUSER2_EMAIL,
                          )
    user2.save()
    campaign1 = Campaign(name=TCAMPAIGN1)
    campaign1.save(username=user.username)
    campaign2 = Campaign(name=TCAMPAIGN2)
    campaign2.save(username=user.username)
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
        forge_relationship(class_=self.campaign2,
                           right_class=self.campaign1,
                           rel_type=TRELATIONSHIP_TYPE,
                           user=self.user.username,
                           rel_confidence=TRELATIONSHIP_CONFIDENCE)
    def tearDown(self):
        clean_db()
    def testCreateRelationship(self):
        relationship1 = self.campaign1.relationships[0]
        relationship2 = self.campaign2.relationships[0]
        self.assertEqual(relationship1.rel_confidence, TRELATIONSHIP_CONFIDENCE)
        self.assertEqual(relationship2.rel_confidence, TRELATIONSHIP_CONFIDENCE)
        self.assertEqual(relationship1.analyst, self.user.username)
        self.assertEqual(relationship2.analyst, self.user.username)
    def testChangingReason(self):
        relationship1 = self.campaign1.relationships[0]
        relationship2 = self.campaign2.relationships[0]
        self.assertEqual(relationship1.rel_reason, "")
        self.assertEqual(relationship2.rel_reason, "")
        update_relationship_reasons(left_class=self.campaign1,
                                    right_class=self.campaign2,
                                    rel_type=TRELATIONSHIP_TYPE,
                                    analyst=self.user2.username,
                                    new_reason=TRELATIONSHIP_NEW_REASON)
        campaign1 = Campaign.objects.get(id=self.campaign1.id)
        campaign2 = Campaign.objects.get(id=self.campaign2.id)
        relationship1 = campaign1.relationships[0]
        relationship2 = campaign2.relationships[0]
        self.assertEqual(relationship1.rel_reason, TRELATIONSHIP_NEW_REASON)
        self.assertEqual(relationship2.rel_reason, TRELATIONSHIP_NEW_REASON)
    def testChangingConfidence(self):
        relationship1 = self.campaign1.relationships[0]
        relationship2 = self.campaign2.relationships[0]
        self.assertEqual(relationship1.rel_confidence, TRELATIONSHIP_CONFIDENCE)
        self.assertEqual(relationship2.rel_confidence, TRELATIONSHIP_CONFIDENCE)
        update_relationship_confidences(left_class=self.campaign1,
                                    right_class=self.campaign2,
                                    rel_type=TRELATIONSHIP_TYPE,
                                    analyst=self.user2.username,
                                    new_confidence=TRELATIONSHIP_NEW_CONFIDENCE)
        self.assertEqual(relationship1.rel_confidence, TRELATIONSHIP_NEW_CONFIDENCE)
        self.assertEqual(relationship2.rel_confidence, TRELATIONSHIP_NEW_CONFIDENCE)
