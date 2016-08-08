import re

from django.test import SimpleTestCase
from django.test.client import RequestFactory, Client

from mongoengine import Document, StringField

from crits.config.config import CRITsConfig
from crits.core.user import CRITsUser
from crits.core.crits_mongoengine import CritsBaseAttributes, CritsQuerySet
from crits.core.crits_mongoengine import CritsSourceDocument
from crits.core.source_access import SourceAccess

# We will be running tests against a bunch of functions from these files
import crits.core.views as views
import crits.core.handlers as handlers


TCOL = "ct_test"
TCOLS = "ct_test_SOURCE"
TSRC = "TestSource"
TUNKSRC = "UnknownSource"
TRANDUSER = "RandomUser"
TUSER_NAME = "test_user"
TUSER_PASS = "!@#j54kfeimn?>S<D"
TUSER_PASS_HASH_RE = re.compile('^[\d\w]+\$(\d+\$)?(\w+\$)?\S+$')
TUSER_EMAIL = "test_user@example.com"
TUSER_FNAME = "Testfirst"
TUSER_LNAME = "Testlast"
TUSER_ROLE = "Administrator"
TOBJS_VALUE = "Test source value"
TOBJ_VALUE = "Test value"
TOBJS_NAME = "tsrcobj"
TOBJ_NAME = "tobj"


def get_config():
    """
    Get the CRITs configuration.

    :returns: :class:`crits.config.config.CRITsConfig`
    """

    crits_config = CRITsConfig.objects().first()
    if not crits_config:
        crits_config = CRITsConfig()
        crits_config.save()
    return crits_config


class TestSourceObject(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    CRITs test object with source
    """

    meta = {
        "collection": TCOLS,
        "crits_type": "TestSourceBase",
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'Name',
            'value': 'Value'
        }
    }
    name = StringField(required=True)
    value = StringField(required=True)


class TestObject(CritsBaseAttributes, Document):
    """
    CRITs test object
    """

    meta = {
        "collection": TCOL,
        "crits_type": "TestBase",
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'Name',
            'value': 'Value'
        }
    }
    name = StringField(required=True)
    value = StringField(required=True)


def prep_db():
    """
    Prep the DB for testing.
    """

    clean_db()
    # Create a new default config
    crits_config = CRITsConfig()
    crits_config.save()
    # Add Source
    handlers.add_new_source(TSRC, TRANDUSER)
    # Add User
    user = CRITsUser.create_user(username=TUSER_NAME,
                                 password=TUSER_PASS,
                                 email=TUSER_EMAIL,
                                 )
    user.first_name = TUSER_FNAME
    user.last_name = TUSER_LNAME
    user.save()
    # Add test source object
    obj = TestSourceObject()
    obj.name = TOBJS_NAME
    obj.value = TOBJS_VALUE
    obj.add_source(source=TSRC, analyst=TUSER_NAME)
    obj.save()
    # Add another with Different source
    obj = TestSourceObject()
    obj.name = TOBJS_NAME
    obj.value = TOBJS_VALUE
    obj.add_source(source=TUNKSRC, analyst=TRANDUSER)
    obj.save()
    # Add test non-source object
    obj = TestObject()
    obj.name = TOBJ_NAME
    obj.value = TOBJ_VALUE
    obj.save()


def clean_db():
    """
    Clean up the DB after testing.
    """

    src = SourceAccess.objects(name=TSRC).first()
    if src:
        src.delete()
    user = CRITsUser.objects(username=TUSER_NAME).first()
    if user:
        user.delete()
    TestObject.drop_collection()
    TestSourceObject.drop_collection()
    CRITsConfig.drop_collection()


class SourceTests(SimpleTestCase):
    """
    Test sources.
    """

    def setUp(self):
        src = SourceAccess.objects(name=TSRC).first()
        if src:
            src.delete()

    def AddSource(self):
        self.assertTrue(handlers.add_new_source(TSRC, TUSER_NAME))

    def FindSource(self):
        self.assertEqual(SourceAccess.objects(name=TSRC).first().name, TSRC)

    def DelSource(self):
        self.assertTrue(SourceAccess.objects(name=TSRC).first())
        SourceAccess.objects(name=TSRC).first().delete()
        self.assertFalse(SourceAccess.objects(name=TSRC).first())

    def testSourceAddDel(self):
        self.AddSource()
        self.FindSource()
        self.DelSource()


class UserTests(SimpleTestCase):
    """
    Test Users.
    """

    def setUp(self):
        user = CRITsUser.objects(username=TUSER_NAME).first()
        if user:
            user.delete()

    def AddUser(self):
        self.user = CRITsUser.create_user(username=TUSER_NAME,
                                          password=TUSER_PASS,
                                          email=TUSER_EMAIL,
                                          )

        self.assertEqual(self.user.username, TUSER_NAME)
        self.assertTrue(TUSER_PASS_HASH_RE.match(self.user.password))
        self.user.first_name = TUSER_FNAME
        self.user.last_name = TUSER_LNAME
        self.user.save()

    def FindUser(self):
        self.assertTrue(CRITsUser.objects(username=TUSER_NAME).first())

    def DelUser(self):
        fuser = CRITsUser.objects(username=TUSER_NAME).first()
        fuser.delete()
        fuser = CRITsUser.objects(username=TUSER_NAME).first()
        self.assertFalse(fuser)

    def testUserAddDel(self):
        self.AddUser()
        self.FindUser()
        self.DelUser()


class DataQueryTests(SimpleTestCase):
    """
    Test Data queries.
    """

    def setUp(self):
        prep_db()
        self.factory = RequestFactory()
        self.req = self.factory.get('/')
        self.user = CRITsUser.objects(username=TUSER_NAME).first()
        self.req.user = self.user

    def tearDown(self):
        clean_db()

    def testCSVQuery(self):
        obj = TestObject
        fields = "status,name,campaign,modified,value"
        resp = handlers.csv_query(obj,
                                  self.user.username,
                                  fields=fields.split(',')
                                  )
        lines = resp.splitlines()
        item = lines[1].split(',')
        self.assertEqual(item[0], "New")
        self.assertEqual(item[1], TOBJ_NAME)
        self.assertEqual(item[4], TOBJ_VALUE)
        self.assertEqual(lines[0], fields)

    def testParseQueryRequest(self):
        fields = ["name", "value", "invalid"]
        sort = "tsort"
        limit = 10
        skip = 5
        self.req = self.factory.get('/?fields=%s&sort=%s&limit=%d&skip=%d' %
                                    (",".join(fields), sort, limit, skip))
        resp = handlers.parse_query_request(self.req, TestObject)
        # Pop invalid off the list, we should not get it back
        fields.pop()
        self.assertEqual(fields, resp['fields'])
        self.assertEqual(sort, resp['sort'])
        self.assertEqual(limit, resp['limit'])
        self.assertEqual(skip, resp['skip'])

    def testSourceCSVQuery(self):
        obj = TestSourceObject
        fields = "status,name,source,modified,value"
        data = {'username': self.user.username,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'email': self.user.email,
                'role': self.user.role,
                'sources': [TSRC, ],
                'organization': TSRC,
                'secret': '',
                'subscriptions': [],
                'totp': False,
                }
        handlers.modify_source_access(self.user.username, data)
        resp = handlers.csv_query(obj,
                                  self.user.username,
                                  fields=fields.split(',')
                                  )
        lines = resp.splitlines()
        item = lines[1].split(',')
        self.assertEqual(item[0], "New")
        self.assertEqual(item[1], TOBJS_NAME)
        self.assertEqual(item[2], TSRC)
        self.assertEqual(item[4], TOBJS_VALUE)
        self.assertEqual(lines[0], fields)

    def testDataQuery(self):
        """
        Test data_query from handlers.py
        data_query(col_obj,user[,limit,skip,sort,query,projection])
        """
        obj = TestObject
        resp = handlers.data_query(obj, self.user.username)
        self.assertEqual(resp['count'], 1)
        self.assertEqual(resp['result'], 'OK')
        self.assertEqual(resp['crits_type'], 'TestBase')
        self.assertEqual(resp['msg'], '')
        self.assertTrue(isinstance(resp['data'], CritsQuerySet))
        self.assertEqual(resp['data'][0].name, TOBJ_NAME)
        self.assertEqual(resp['data'][0].value, TOBJ_VALUE)
        self.assertEqual(resp['data'][0]._meta['crits_type'], "TestBase")

    def testSourceDataQuery(self):
        objs = TestSourceObject
        # User does not have source, should not return results
        resp = handlers.data_query(objs, self.user.username)
        self.assertEqual(resp['count'], 0)
        self.assertEqual(resp['result'], 'OK')
        self.assertEqual(resp['crits_type'], 'TestSourceBase')
        self.assertEqual(resp['msg'], '')
        self.assertTrue(isinstance(resp['data'], CritsQuerySet))
        # Add source for user and query again
        data = {'username': self.user.username,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'email': self.user.email,
                'role': self.user.role,
                'sources': [TSRC, ],
                'secret': '',
                'organization': TSRC,
                'subscriptions': [],
                'totp': False,
                }
        handlers.modify_source_access(self.user.username, data)
        resp = handlers.data_query(objs, self.user.username)
        # Now we should get one result, but not the UnknownSource object
        self.assertEqual(resp['count'], 1)
        self.assertEqual(resp['result'], 'OK')
        self.assertEqual(resp['crits_type'], 'TestSourceBase')
        self.assertEqual(resp['msg'], '')
        self.assertEqual(resp['data'][0].name, TOBJS_NAME)
        self.assertEqual(resp['data'][0].value, TOBJS_VALUE)
        self.assertEqual(resp['data'][0]._meta['crits_type'], "TestSourceBase")


class LoginTests(SimpleTestCase):
    """
    Test authentication.
    """

    def setUp(self):
        prep_db()
        self.factory = RequestFactory()
        self.client = Client()
        self.user = CRITsUser.objects(username=TUSER_NAME).first()

    def tearDown(self):
        clean_db()

    def testUnauth(self):
        redir_url = 'http://testserver/login/?next='
        # These should all start and end with a /
        paths = [
            "/",
            "/dashboards/",
            #"/nourl/",  # Does not work, see issue #1147.
            "/samples/details/d41d8cd98f00b204e9800998ecf8427e/",
        ]

        for path in paths:
            response = self.client.get(path, follow=True)
            redirs = response.redirect_chain
            self.assertEquals(response.status_code, 200)
            self.assertTrue(redirs[0][0] in redir_url + path)
            self.assertEquals(redirs[0][1], 302)

    def testBasicLogin(self):
        pass

    def testLDAPLogin(self):
        pass

    def testRemoteUser(self):
        pass

    def testTOTP(self):
        pass


class DashboardViewTests(SimpleTestCase):
    """
    Test dashboard rendering.
    """

    def setUp(self):
        prep_db()
        self.factory = RequestFactory()
        self.req = self.factory.get('/dashboard/')
        self.user = CRITsUser.objects(username=TUSER_NAME).first()
        self.req.user = self.user

    def tearDown(self):
        clean_db()

    def testTopBar(self):
        response = views.dashboard(self.req)
        self.assertTrue(">{0} {1}</a>".format(self.user.first_name,
                                              self.user.last_name)
                        in response.content)
        self.assertTrue("&nbsp;({0})".format(self.user.role)
                        in response.content)

    def testUserInactiveRedirect(self):
        self.req.user.mark_inactive()
        response = views.dashboard(self.req)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("/login/?next=/dashboard/" in response['Location'])
        self.req.user.mark_active()
        response = views.dashboard(self.req)
        self.assertEqual(response.status_code, 200)
