from django.test import SimpleTestCase
from django.test.client import RequestFactory

import crits.emails.views as views
import crits.emails.handlers as handlers
from crits.core.user import CRITsUser
from crits.core.handlers import add_new_source
from crits.core.source_access import SourceAccess

TSRC = "TestSource"
TUSER_NAME = "test_user"
TUSER_PASS = "!@#j54kfeimn?>S<D"
TUSER_EMAIL = "test_user@example.com"
TUSER_ROLE = "Administrator"

EM_REF = ""
EM_SRC = TSRC
EM_METH = ""

# Not starting this on a separate line because that breaks the EML parser.
EML_DATA = """x-store-info:sbevkl2QZR7OXo7WID5ZcVBK1Phj2jX/
Authentication-Results: hotmail.com; sender-id=none (sender IP is 98.138.90.157) header.from=sanjeerly@yahoo.com; dkim=pass (testing mode) header.d=yahoo.com; x-hmca=pass
X-SID-PRA: sanjeerly@yahoo.com
X-SID-Result: None
X-DKIM-Result: Pass(t)
X-AUTH-Result: PASS
X-Message-Status: n:n
X-Message-Delivery: Vj0xLjE7dXM9MDtsPTA7YT0xO0Q9MTtHRD0xO1NDTD0w
X-Message-Info: gamVN+8Ez8V+RHg+F+brAWseB3gKupOiF1HhBKvBFwkh/MnMBSYr9tg0qsxeDfsJLtFcOu9pxCBOEw6pLeEQwUe09i47LD+O1NxlrU6W+IdHONEqL12870AgmD/1L7IzM4iscTQgjn8=
Received: from nm9-vm2.bullet.mail.ne1.yahoo.com ([98.138.90.157]) by BAY0-MC4-F10.Bay0.hotmail.com with Microsoft SMTPSVC(6.0.3790.4900);
	 Mon, 27 Aug 2012 19:22:17 -0700
Received: from [98.138.90.48] by nm9.bullet.mail.ne1.yahoo.com with NNFMP; 28 Aug 2012 02:22:17 -0000
Received: from [98.138.226.168] by tm1.bullet.mail.ne1.yahoo.com with NNFMP; 28 Aug 2012 02:22:17 -0000
Received: from [127.0.0.1] by omp1069.mail.ne1.yahoo.com with NNFMP; 28 Aug 2012 02:22:17 -0000
X-Yahoo-Newman-Property: ymail-3
X-Yahoo-Newman-Id: 62808.64696.bm@omp1069.mail.ne1.yahoo.com
Received: (qmail 83522 invoked by uid 60001); 28 Aug 2012 02:22:17 -0000
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=yahoo.com; s=s1024; t=1346120536; bh=JisZZrEeT9oXnpemRReNB+AHA9KkSpl9mBrb153Y+3k=; h=X-YMail-OSG:Received:X-Mailer:References:Message-ID:Date:From:Reply-To:Subject:To:In-Reply-To:MIME-Version:Content-Type; b=g3tOd1WmlC95e/lejBs+ZKH7vJNFx81jdC1VDSdwdwPD7EyrS2XeUVBBtOUHlrOFc661uL2bR6UhXoiGZoRloAG7TlO+ik3m/1dfngTxTflfMOUTRmnOjLmZrj7Cg5qjdRQSZHSdBOJ9BxmvfYgyGeG7COvC555PVZvCTsep8H0=
DomainKey-Signature:a=rsa-sha1; q=dns; c=nofws;
  s=s1024; d=yahoo.com;
  h=X-YMail-OSG:Received:X-Mailer:References:Message-ID:Date:From:Reply-To:Subject:To:In-Reply-To:MIME-Version:Content-Type;
  b=rjJ2Zza8PyNJEhKGYQQhK5ldw8Kj7UyK+uWmwsRlFOatoe/ARnV6SRACOQm3Np0OpWiG6MEeqk2Hvxqd4jpTW1xzRaAZ/ibxsg4kKeTq8hQ7/XTxcV57IRMbdjrL2jh4iAbB5Xqhow07iPFo7AwjD5Gcd02/SIefq+SHHTtLPcI=;
X-YMail-OSG: .RhCBEsVM1n3_zMO0Dkx8MQxTkzyNiqWEMVjxbolfW48PkF
 Xt6CPEqAM6Z1AEgzA7lWeuiqUiBy7cNZzL35G4s7vVA3BrE_CHtz8pMhQ6VT
 zFXmZIPwsjmBu29QyW.J3_ZkEzBXQ04mFHAJIoB4CLYKLpLlWi8KNch.dWfr
 MJxlg9PbUjX6hkruhb2ok8Z0doq_JvWKVOnexUcC3kDrZsXqgs1cCPaqV2hl
 h79egajx62aFgQFmusX.suL371ubS8YoH5nzIfKS1OWTPSc0bxZBrHe46dWq
 EccTjsS119mSyCDsC1fbFT9m0o.dxBp32iInNn1Y5pT6tCqAvA3JdN2VTyVc
 kJGTx4Z.DPhfS2QTscPCvIwjDA2QTeJ2KRT.etdtY2.ymroP2RYV7kcAE8.2
 Y6oHy.MLDIUhrmjVBWG6quuua_g--
Received: from [117.71.245.60] by web121303.mail.ne1.yahoo.com via HTTP; Mon, 27 Aug 2012 19:22:16 PDT
X-Mailer: YahooMailWebService/0.8.121.416
References: <CAGVv_bMdcDgG3i7hZsRArAKKDiT1=vHUDkzj7bz4jY4zFS3tdQ@mail.gmail.com>
Message-ID: <1346120536.82002.YahooMailNeo@web121303.mail.ne1.yahoo.com>
Date: Mon, 27 Aug 2012 19:22:16 -0700 (PDT)
From: Sanjeer Ly <sanjeerly@yahoo.com>
Reply-To: Sanjeer Ly <sanjeerly@yahoo.com>
Subject:  photo
To: "hasan209@hotmail.com" <hasan209@hotmail.com>,
  "anargulbulak@hotmail.com" <anargulbulak@hotmail.com>,
  "yaghlaqar@yahoo.com" <yaghlaqar@yahoo.com>,
  "curtis115@hotmail.com" <curtis115@hotmail.com>,
  "igamberdi@westnet.com.au" <igamberdi@westnet.com.au>,
  "a.karluki@hotmail.com" <a.karluki@hotmail.com>,
  "askartarim@hotmail.com" <askartarim@hotmail.com>
In-Reply-To: <CAGVv_bMdcDgG3i7hZsRArAKKDiT1=vHUDkzj7bz4jY4zFS3tdQ@mail.gmail.com>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="1837502048-29993827-1346120536=:82002"
Return-Path: sanjeerly@yahoo.com
X-OriginalArrivalTime: 28 Aug 2012 02:22:17.0243 (UTC) FILETIME=[F1B766B0:01CD84C3]

--1837502048-29993827-1346120536=:82002
Content-Type: multipart/alternative; boundary="1837502048-920500242-1346120536=:82002"

--1837502048-920500242-1346120536=:82002
Content-Type: text/plain; charset=iso-8859-1
Content-Transfer-Encoding: quoted-printable

=A0
--1837502048-920500242-1346120536=:82002--
"""

def prep_db():
    """
    Prep the database for the test.
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
    Clean the database before/after the test.
    """

    src = SourceAccess.objects(name=TSRC).first()
    if src:
        src.delete()
    user = CRITsUser.objects(username=TUSER_NAME).first()
    if user:
        user.delete()


class EmailHandlerTests(SimpleTestCase):
    """
    Email test class.
    """

    def setUp(self):
        prep_db()
        self.factory = RequestFactory()
        self.user = CRITsUser.objects(username=TUSER_NAME).first()
        self.user.sources.append(TSRC)
        self.user.save()

    def tearDown(self):
        clean_db()

    def testEmailRawAdd(self):
        result = handlers.handle_pasted_eml(EML_DATA, TSRC, None, self.user, "Test")
        self.assertEqual(result['status'], True)
        self.assertEqual(result['data']['x_mailer'],"YahooMailWebService/0.8.121.416")
        newdata = ""
        for line in EML_DATA.split('\n'):
            newdata += line.lstrip() + "\n"
        result = handlers.handle_pasted_eml(newdata, TSRC, None, self.user, "Test")
        self.assertEqual(result['status'], True)
        self.assertEqual(result['data']['x_mailer'],"YahooMailWebService/0.8.121.416")

    def testEmailAdd(self):
        result = handlers.handle_eml(EML_DATA, TSRC, None, self.user, "Test")
        self.assertEqual(result['status'], True)
        self.assertEqual(result['data']['x_mailer'],"YahooMailWebService/0.8.121.416")


class EmailViewTests(SimpleTestCase):
    """
    Test email views.
    """

    def setUp(self):
        prep_db()
        self.factory = RequestFactory()
        self.user = CRITsUser.objects(username=TUSER_NAME).first()
        self.user.sources.append(TSRC)
        self.user.save()
        # Add a test email
        handlers.handle_eml(EML_DATA, TSRC, None, self.user, "Test")

    def tearDown(self):
        clean_db()

    def testEmailsList(self):
        self.req = self.factory.get('/emails/list/')
        self.req.user = self.user
        response = views.emails_listing(self.req)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("#email_listing" in response.content)

    def testEmailsjtList(self):
        self.req = self.factory.post('/emails/list/jtlist/',
                                     {},
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.req.user = self.user
        response = views.emails_listing(self.req, 'jtlist')
        self.assertEqual(response.status_code, 200)
