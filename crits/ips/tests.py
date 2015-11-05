from django.test import SimpleTestCase
from django.test.client import RequestFactory

import crits.ips.views as views
import crits.ips.handlers as handlers
from crits.ips.ip import IP
from crits.core.user import CRITsUser
from crits.core.handlers import add_new_source
from crits.core.source_access import SourceAccess
from crits.vocabulary.ips import IPTypes

TSRC = "TestSource"
TUSER_NAME = "test_user"
TUSER_PASS = "!@#j54kfeimn?>S<D"
TUSER_EMAIL = "test_user@example.com"
TUSER_ROLE = "Administrator"

IP_REF = ""
IP_SRC = TSRC
IP_METH = ""
IPADDR = "127.0.0.1"
IP_TYPE = IPTypes.IPV4_ADDRESS
IP_LIST = ["test", "test two"]
IP_BUCKET = ",".join(IP_LIST)
IP_TICKET = IP_LIST


def prep_db():
    """
    Prep the DB for the test.
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
    Clean the DB from the test.
    """

    src = SourceAccess.objects(name=TSRC).first()
    if src:
        src.delete()
    user = CRITsUser.objects(username=TUSER_NAME).first()
    if user:
        user.delete()


class IPHandlerTests(SimpleTestCase):
    """
    Test IP handlers.
    """

    def setUp(self):
        prep_db()
        self.factory = RequestFactory()
        self.user = CRITsUser.objects(username=TUSER_NAME).first()
        self.user.sources.append(TSRC)
        self.user.save()

    def tearDown(self):
        clean_db()

    def testIPAdd(self):
        data = {
            'source_reference': IP_REF,
            'source': IP_SRC,
            'ip_type': IP_TYPE,
            'ip': IPADDR,
            'analyst': TUSER_NAME,
            'bucket_list': IP_BUCKET,
            'ticket': IP_TICKET,
        }
        errors = []
        (result, errors, retVal) = handlers.add_new_ip(data, rowData={},
                                                       request=self.factory,
                                                       errors="")
        self.assertTrue(result)
        self.assertTrue(retVal['success'])

    def testIPGet(self):
        self.assertEqual(IP.objects(ip=IPADDR).count(), 1)

        ip = IP.objects(ip=IPADDR).first()
        self.assertEqual(ip.ip, IPADDR)
        self.assertEqual(set(ip.bucket_list), set(IP_LIST))
        self.assertTrue(ip.tickets[0]['ticket_number'] in IP_LIST)


class IPViewTests(SimpleTestCase):
    """
    Test IP Views.
    """

    def setUp(self):
        prep_db()
        self.factory = RequestFactory()
        self.user = CRITsUser.objects(username=TUSER_NAME).first()
        self.user.sources.append(TSRC)
        self.user.save()
        data = {
            'source_reference': IP_REF,
            'source': IP_SRC,
            'ip_type': IP_TYPE,
            'ip': IPADDR,
            'analyst': TUSER_NAME,
            'bucket_list': IP_BUCKET,
            'ticket': IP_TICKET,
        }
        errors = []
        (result, errors, retVal) = handlers.add_new_ip(data, rowData={},
                                                       request=self.factory,
                                                       errors="")

    def tearDown(self):
        clean_db()

    def testUserInactiveRedirect(self):
        self.req = self.factory.get('/ips/list/')
        self.req.user = self.user
        self.req.user.mark_inactive()
        response = views.ips_listing(self.req)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("/login/?next=/ips/list/" in response['Location'])
        self.req.user.mark_active()
        response = views.ips_listing(self.req)
        self.assertEqual(response.status_code, 200)

    def testIPsList(self):
        self.req = self.factory.get('/ips/list/')
        self.req.user = self.user
        response = views.ips_listing(self.req)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("#ip_listing" in response.content)

    def testIPsjtList(self):
        self.req = self.factory.post('/ips/list/jtlist/',
                                     {},
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.req.user = self.user
        response = views.ips_listing(self.req, 'jtlist')
        self.assertEqual(response.status_code, 200)
