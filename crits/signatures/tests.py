from django.test import SimpleTestCase
from django.test.client import RequestFactory

import crits.signatures.views as views
import crits.signatures.handlers as handlers
from crits.core.user import CRITsUser
from crits.core.handlers import add_new_source
from crits.signatures.handlers import add_new_signature_type, handle_signature_file
from crits.core.source_access import SourceAccess

TSRC = "TestSource"
TDT = "Yara"
TUSER_NAME = "test_user"
TUSER_PASS = "!@#j54kfeimn?>S<D"
TUSER_EMAIL = "test_user@example.com"
TUSER_ROLE = "Administrator"

SIGNATURE_TITLE = "Test Signature Title"
SIGNATURE_DESCRIPTION = "Test Signature Description"
SIGNATURE_DATA = "Test Signature Data"

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
    # Add Source
    add_new_source(TSRC, TUSER_NAME)
    # Add Data Type
    add_new_signature_type(TDT, TUSER_NAME)

def clean_db():
    """
    Clean database for test.
    """

    src = SourceAccess.objects(name=TSRC).first()
    if src:
        src.delete()
    user = CRITsUser.objects(username=TUSER_NAME).first()
    if user:
        user.delete()


class SignatureHandlerTests(SimpleTestCase):
    """
    Test Signature Handlers
    """

    def setUp(self):
        prep_db()
        self.factory = RequestFactory()
        self.user = CRITsUser.objects(username=TUSER_NAME).first()
        self.user.sources.append(TSRC)
        self.user.save()

    def tearDown(self):
        clean_db()

    def testSignatureAdd(self):
        title = SIGNATURE_TITLE
        description = SIGNATURE_DESCRIPTION
        data = SIGNATURE_DATA
        data_type = TDT
        source_name = TSRC
        user = TUSER_NAME
        (status) = handlers.handle_signature_file(data, source_name, user, description, title, data_type)


class SignatureViewTests(SimpleTestCase):
    """
    Test Signature Views
    """

    def setUp(self):
        prep_db()
        self.factory = RequestFactory()
        self.user = CRITsUser.objects(username=TUSER_NAME).first()
        self.user.sources.append(TSRC)
        self.user.save()
        # Add a test signature
        title = SIGNATURE_TITLE
        description = SIGNATURE_DESCRIPTION
        data = SIGNATURE_DATA
        data_type = TDT
        source_name = TSRC
        user = TUSER_NAME
        (status) = handlers.handle_signature_file(data, source_name, user, description, title, data_type)

    def tearDown(self):
        clean_db()

    def testUserInactiveRedirect(self):
        self.req = self.factory.get('/signatures/list/')
        self.req.user = self.user
        self.req.user.mark_inactive()
        response = views.signatures_listing(self.req)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("/login/?next=/signatures/list/" in response['Location'])
        self.req.user.mark_active()
        response = views.signatures_listing(self.req)
        self.assertEqual(response.status_code, 200)

    def testSignaturesList(self):
        self.req = self.factory.get('/signatures/list/')
        self.req.user = self.user
        response = views.signatures_listing(self.req)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("#signature_listing" in response.content)

    def testSignaturesjtList(self):
        self.req = self.factory.post('/signatures/list/jtlist/',
                                     {},
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.req.user = self.user
        response = views.signatures_listing(self.req, 'jtlist')
        self.assertEqual(response.status_code, 200)