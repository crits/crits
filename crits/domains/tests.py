from django.test import SimpleTestCase
from django.test.client import RequestFactory

import crits.domains.views as views
import crits.domains.handlers as handlers
from crits.core.user import CRITsUser
from crits.core.handlers import add_new_source
from crits.core.source_access import SourceAccess

TSRC = "TestSource"
TUSER_NAME = "test_user"
TUSER_PASS = "!@#j54kfeimn?>S<D"
TUSER_EMAIL = "test_user@example.com"
TUSER_ROLE = "Administrator"

DOM_REF = ""
DOM_SRC = TSRC
DOM_METH = ""
DOMAIN = "example.com"

def prep_db():
    """
    Prep database for test.
    """

    clean_db()
    # Add Source
    add_new_source(TSRC, "RandomUser")
    # Add User
    user = CRITsUser.create_user(
                          username=TUSER_NAME,
                          password=TUSER_PASS,
                          email=TUSER_EMAIL,
                          )
    user.save()


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


class DomainHandlerTests(SimpleTestCase):
    """
    Test Domain Handlers
    """

    def setUp(self):
        prep_db()
        self.factory = RequestFactory()
        self.user = CRITsUser.objects(username=TUSER_NAME).first()
        self.user.sources.append(TSRC)
        self.user.save()


    def tearDown(self):
        clean_db()

    def testDomainAdd(self):
        data = {
                'domain_reference': DOM_REF,
                'domain_source': DOM_SRC,
                'domain_method': DOM_METH,
                'domain': DOMAIN,
                }
        errors = []
        (result, errors, retVal) = handlers.add_new_domain(data, self, errors)



class DomainViewTests(SimpleTestCase):
    """
    Test Domain Views
    """

    def setUp(self):
        prep_db()
        self.factory = RequestFactory()
        self.user = CRITsUser.objects(username=TUSER_NAME).first()
        self.user.sources.append(TSRC)
        self.user.save()
        # Add a test domain
        data = {
                'domain_reference': DOM_REF,
                'domain_source': DOM_SRC,
                'domain_method': DOM_METH,
                'domain': DOMAIN,
                }
        errors = []
        (result, errors, retVal) = handlers.add_new_domain(data, self, errors)

    def tearDown(self):
        clean_db()

    def testUserInactiveRedirect(self):
        self.req = self.factory.get('/domains/list/')
        self.req.user = self.user
        self.req.user.mark_inactive()
        response = views.domains_listing(self.req)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("/login/?next=/domains/list/" in response['Location'])
        self.req.user.mark_active()
        response = views.domains_listing(self.req)
        self.assertEqual(response.status_code, 200)

    def testDomainsList(self):
        self.req = self.factory.get('/domains/list/')
        self.req.user = self.user
        response = views.domains_listing(self.req)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("#domain_listing" in response.content)

    def testDomainsjtList(self):
        self.req = self.factory.post('/domains/list/jtlist/',
                                     {},
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.req.user = self.user
        response = views.domains_listing(self.req, 'jtlist')
        self.assertEqual(response.status_code, 200)
