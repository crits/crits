#-------------
# Some sections of the code below have been copied from
# MongoEngine.
#
# https://github.com/MongoEngine/mongoengine
#
# Copyright (c) 2009 See AUTHORS
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#-------------

import datetime
import hmac
import logging
import random
import re
import string
import time
import uuid

from hashlib import sha1
from mongoengine import Document, EmbeddedDocument
from mongoengine import StringField, DateTimeField, ListField
from mongoengine import BooleanField, ObjectIdField, EmailField
from mongoengine import EmbeddedDocumentField, IntField
from mongoengine import DictField, DynamicEmbeddedDocument
from mongoengine.django.utils import datetime_now
#from mongoengine.django.auth import SiteProfileNotAvailable

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.hashers import check_password, make_password
#from django.contrib.auth.models import _user_has_perm, _user_get_all_permissions
#from django.contrib.auth.models import _user_has_module_perms
from django.core.exceptions import ImproperlyConfigured
from django.db import models
#from django.utils.translation import ugettext_lazy as _

from crits.config.config import CRITsConfig
from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument
from crits.core.crits_mongoengine import CritsDocumentFormatter, UnsupportedAttrs
from crits.core.user_migrate import migrate_user



logger = logging.getLogger(__name__)


class EmbeddedSubscription(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Subscription
    """

    _id = ObjectIdField(required=True, db_field="id")
    date = DateTimeField(default=datetime.datetime.now)


class EmbeddedSourceSubscription(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Subscription
    """

    date = DateTimeField(default=datetime.datetime.now)
    name = StringField(required=True)


class EmbeddedFavorites(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Favorites
    """

    Actor = ListField(StringField())
    Backdoor = ListField(StringField())
    Campaign = ListField(StringField())
    Certificate = ListField(StringField())
    Domain = ListField(StringField())
    Email = ListField(StringField())
    Event = ListField(StringField())
    Exploit = ListField(StringField())
    IP = ListField(StringField())
    Indicator = ListField(StringField())
    PCAP = ListField(StringField())
    RawData = ListField(StringField())
    Sample = ListField(StringField())
    Screenshot = ListField(StringField())
    Signature = ListField(StringField())
    Target = ListField(StringField())

class EmbeddedSubscriptions(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Subscriptions
    """

    Actor = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    Backdoor = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    Campaign = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    Certificate = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    Domain = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    Email = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    Event = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    Exploit = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    IP = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    Indicator = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    PCAP = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    RawData = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    Sample = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    Signature = ListField(EmbeddedDocumentField(EmbeddedSubscription))
    Source = ListField(EmbeddedDocumentField(EmbeddedSourceSubscription))
    Target = ListField(EmbeddedDocumentField(EmbeddedSubscription))


class PreferencesField(DynamicEmbeddedDocument):
    """
    Embedded User Preferences
    """

    notify = DictField(required=True, default=
                       {"email": False}
                       )

    plugins = DictField(required=False, default={})

    ui = DictField(required=True, default=
                   {"theme": "default",
                    "table_page_size": 25
                    }
                   )

    nav = DictField(required=True, default={"nav_menu": "default",
                                            "text_color": "#FFF",
                                            "background_color": "#464646",
                                            "hover_text_color": "#39F",
                                            "hover_background_color": "#6F6F6F"})

    toast_notifications = DictField(required=True, default={"enabled": True,
                                                            "acknowledgement_type": "sticky",
                                                            "initial_notifications_display": "show",
                                                            "newer_notifications_location": "top"})

class EmbeddedPasswordReset(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Password Reset
    """

    reset_code = StringField(required=True, default="")
    attempts = IntField(default=0)
    date = DateTimeField(default=datetime.datetime.now)


class EmbeddedLoginAttempt(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Login Attempt
    """

    success = BooleanField(required=True)
    user_agent = StringField(required=True)
    remote_addr = StringField(required=True)
    accept_language = StringField(required=True)
    date = DateTimeField(default=datetime.datetime.now)


class EmbeddedAPIKey(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded API Key
    """

    name = StringField(required=True)
    api_key = StringField(required=True)
    date = DateTimeField(default=datetime.datetime.now)
    default = BooleanField(default=False)


class CRITsUser(CritsDocument, CritsSchemaDocument, Document):
    """
    CRITs User object
    """

    meta = {
        "collection": settings.COL_USERS,
        'indexes': [
            {'fields': ['username'],
             'unique': True,
             'sparse': True,
            },
        ],
        "crits_type": 'User',
        "latest_schema_version": 3,
        "schema_doc": {
            'username': 'The username of this analyst',
            'organization': 'The name of the organization this user is from',
            'role': 'The role this user has been granted from a CRITs Admin',
            'sources': ('List [] of source names this user has been granted'
                        ' access to view data from'),
            'subscriptions': {
                'Campaign': [
                    {
                        'date': 'ISODate subscribed',
                        'id': 'ObjectId of the object subscribed to'
                    }
                ],
                'Domain': [
                    {
                        'date': 'ISODate subscribed',
                        'id': 'ObjectId of the object subscribed to'
                    }
                ],
                'Email': [
                    {
                        'date': 'ISODate subscribed',
                        'id': 'ObjectId of the object subscribed to'
                    }
                ],
                'Target': [
                    {
                        'date': 'ISODate subscribed',
                        'id': 'ObjectId of the object subscribed to'
                    }
                ],
                'Event': [
                    {
                        'date': 'ISODate subscribed',
                        'id': 'ObjectId of the object subscribed to'
                    }
                ],
                'IP': [
                    {
                        'date': 'ISODate subscribed',
                        'id': 'ObjectId of the object subscribed to'
                    }
                ],
                'Indicator': [
                    {
                        'date': 'ISODate subscribed',
                        'id': 'ObjectId of the object subscribed to'
                    }
                ],
                'PCAP': [
                    {
                        'date': 'ISODate subscribed',
                        'id': 'ObjectId of the object subscribed to'
                    }
                ],
                'Sample': [
                    {
                        'date': 'ISODate subscribed',
                        'id': 'ObjectId of the object subscribed to'
                    }
                ],
                'Source': [
                    {
                        'date': 'ISODate subscribed',
                        'name': 'Name of the source subscribed to'
                    }
                ],
            },
            'favorites': {
                'Actor': [],
                'Backdoor': [],
                'Campaign': [],
                'Domain': [],
                'Email': [],
                'Target': [],
                'Event': [],
                'Exploit': [],
                'IP': [],
                'Indicator': [],
                'PCAP': [],
                'Sample': [],
            }
        },
    }

    username = StringField(max_length=30, required=True,
                           verbose_name='username',
                           help_text="Required. 30 characters or fewer. Letters, numbers and @/./+/-/_ characters")

    first_name = StringField(max_length=30,
                             verbose_name='first name')

    last_name = StringField(max_length=30,
                            verbose_name='last name')
    email = EmailField(verbose_name='e-mail address')
    password = StringField(max_length=128,
                           verbose_name='password',
                           help_text="Use '[algo]$[iterations]$[salt]$[hexdigest]' or use the <a href=\"password/\">change password form</a>.")
    secret = StringField(verbose_name='TOTP Secret')
    is_staff = BooleanField(default=False,
                            verbose_name='staff status',
                            help_text="Designates whether the user can log into this admin site.")
    is_active = BooleanField(default=True,
                             verbose_name='active',
                             help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.")
    is_superuser = BooleanField(default=False,
                                verbose_name='superuser status',
                                help_text="Designates that this user has all permissions without explicitly assigning them.")
    last_login = DateTimeField(default=datetime_now,
                               verbose_name='last login')
    date_joined = DateTimeField(default=datetime_now,
                                verbose_name='date joined')

    invalid_login_attempts = IntField(default=0)
    login_attempts = ListField(EmbeddedDocumentField(EmbeddedLoginAttempt))
    organization = StringField(default=settings.COMPANY_NAME)
    password_reset = EmbeddedDocumentField(EmbeddedPasswordReset, default=EmbeddedPasswordReset())
    role = StringField(default="Analyst")
    sources = ListField(StringField())
    subscriptions = EmbeddedDocumentField(EmbeddedSubscriptions, default=EmbeddedSubscriptions())
    favorites = EmbeddedDocumentField(EmbeddedFavorites, default=EmbeddedFavorites())
    prefs = EmbeddedDocumentField(PreferencesField, default=PreferencesField())
    totp = BooleanField(default=False)
    secret = StringField(default="")
    api_keys = ListField(EmbeddedDocumentField(EmbeddedAPIKey))
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    defaultDashboard = ObjectIdField(required=False, default=None)


    def migrate(self):
        """
        Migrate to latest schema version.
        """

        migrate_user(self)

    def __setattr__(self, name, value):
        """
        Overrides our core __setattr__ because we have to allow for extra
        authentication attributes that would normally get moved to
        unsupported_attrs.
        """

        if (not self._dynamic and hasattr(self, 'unsupported_attrs')
            and not name in self._fields and not name.startswith('_')
            and not name.startswith('$') and not '.' in name
            and name not in ('backend')):
            if not self.unsupported_attrs:
                self.unsupported_attrs = UnsupportedAttrs()
            self.unsupported_attrs.__setattr__(name, value)
        else:
            super(CritsDocument, self).__setattr__(name, value)

    @property
    def pk(self):
        """
        Return the ObjectId as the primary key.
        """

        return self.id

    def __str__(self):
        """
        This is so request.user returns the username like Django expects,
        not the whole object.
        """

        if self.username:
            return self.username

    # the rest of this taken from the MongoEngine User class.

    def __unicode__(self):
        """
        This is so request.user returns the username like Django expects,
        not the whole object.
        """

        return self.username

    def get_full_name(self):
        """
        Returns the users first and last names, separated by a space.
        """

        full_name = u'%s %s' % (self.first_name or '', self.last_name or '')
        return full_name.strip()

    def is_anonymous(self):
        """
        We do not allow anonymous users.
        """

        return False

    def is_authenticated(self):
        """
        If we know about the user from the request, it means they've
        authenticated.
        """

        return True

    def mark_active(self, analyst=None):
        """
        Mark the user as active.
        """

        self.is_active = True
        self.save(username=analyst)
        return self

    def mark_inactive(self, analyst=None):
        """
        Deactivate the user.
        """

        self.is_active = False
        self.save(username=analyst)
        return self

    def is_password_complex(self, password):
        """
        Based on the CRITsConfig, is the password provided complex enough to be
        used?

        :param password: The password to check for complexity.
        :type password: str
        :returns: True, False
        """

        crits_config = CRITsConfig.objects().first()
        if crits_config:
            pw_regex = crits_config.password_complexity_regex
        else:
            pw_regex = settings.PASSWORD_COMPLEXITY_REGEX
        complex_regex = re.compile(pw_regex)
        if complex_regex.match(password):
            return True
        return False

    def set_password(self, raw_password, analyst=None):
        """
        Sets the user's password - always use this rather than directly
        assigning to :attr:`~mongoengine.django.auth.User.password` as the
        password is hashed before storage.

        :param raw_password: The password to hash and store.
        :type raw_password: str
        :returns: self, False
        """

        if self.is_password_complex(raw_password):
            self.password = make_password(raw_password)
            self.save(username=analyst)
            return self
        else:
            return False

    def set_reset_code(self, analyst):
        """
        Sets a reset code on the account for password reset validation.

        :returns: str
        """

        e = EmbeddedPasswordReset()
        char_set = string.ascii_uppercase + string.digits
        e.reset_code = ''.join(random.sample(char_set*6,6))
        e.date = datetime.datetime.now()
        self.password_reset = e
        self.save(username=analyst)
        return e.reset_code

    def reset_password(self, rcode, new_p, new_p_c, analyst):
        """
        Reset the user's password. Validate the reset code, ensure the two
        passwords are identical, and then set.

        :param rcode: Reset Code to validate.
        :type rcode: str
        :param new_p: New password.
        :type new_p: str
        :param new_p_c: New password confirmation.
        :type new_p_c: str
        :param analyst: The user.
        :type analyst: str
        :returns: dict with keys "success" (boolean) and "message" (str).
        """

        if self.validate_reset_code(rcode, analyst)['success']:
            if new_p == new_p_c:
                self.password_reset.reset_code = ""
                if self.set_password(new_p):
                    return {'success': True, 'message': 'Password reset.'}
                else:
                    crits_config = CRITsConfig.objects().first()
                    if crits_config:
                        pw_desc = crits_config.password_complexity_desc
                    else:
                        pw_desc = settings.PASSWORD_COMPLEXITY_DESC
                    message = 'Password not complex enough: %s' % pw_desc
                    return {'success': False, 'message': message}
            else:
                return {'success': False, 'message': 'Passwords do not match.'}
        else:
            self.password_reset.reset_code = ""
            self.save(username=analyst)
            return {'success': False, 'message': 'Reset Code Expired.'}

    def validate_reset_code(self, reset_code, analyst):
        """
        Validate the reset code. Also ensure that the reset code hasn't expired
        already since it is a limited-time use reset.

        :param reset_code: The reset code.
        :type reset_code: str
        :param analyst: The user.
        :type analyst: str
        :returns: dict with keys "success" (boolean) and "message" (str).
        """

        my_reset = self.password_reset.reset_code
        if len(reset_code) == 6 and len(my_reset) == 6 and my_reset == reset_code:
            date = datetime.datetime.now()
            diff = date - self.password_reset.date
            window = divmod(diff.days * 86400 + diff.seconds, 60)
            if window[0] < 5:
                self.password_reset.attempts = 0
                self.save(username=analyst)
                return {'success': True, 'message': 'Reset Code Validated.'}
            else:
                self.password_reset.attempts += 1
                self.password_reset.reset_code = ""
                self.save(username=analyst)
                return {'success': False, 'message': 'Reset Code Expired.'}
        self.password_reset.attempts += 1
        if self.password_reset.attempts > 2:
            self.password_reset.date = self.password_reset.date + datetime.timedelta(minutes=-5)
            self.save(username=analyst)
            return {'success': False, 'message': 'Reset Code Expired.'}
        self.save(username=analyst)
        return {'success': False, 'message': 'Reset Code Invalid.'}

    def check_password(self, raw_password):
        """
        Checks the user's password against a provided password - always use
        this rather than directly comparing to
        :attr:`~mongoengine.django.auth.User.password` as the password is
        hashed before storage.
        """

        return check_password(raw_password, self.password)

    def create_api_key(self, name, analyst, default=False):
        """
        Generate an API key for the user. It will require a name as we allow for
        unlimited API keys and users need a way to reference them.

        :param name: The name for the API key.
        :type name: str
        :param analyst: The user.
        :type analyst: str
        :param default: Use as default API key.
        :type default: boolean
        :returns: dict with keys "success" (boolean) and "message" (str).
        """

        if not name:
            return {'success': False, 'message': 'Need a name'}
        new_uuid = uuid.uuid4()
        key = hmac.new(new_uuid.bytes, digestmod=sha1).hexdigest()
        ea = EmbeddedAPIKey(name=name, api_key=key, default=default)
        if len(self.api_keys) < 1:
            ea.default = True
        self.api_keys.append(ea)
        self.save(username=analyst)
        return {'success': True, 'message': {'name': name,
                                             'key': key,
                                             'date': str(ea.date)}}

    def default_api_key(self, name, analyst):
        """
        Make an API key the default key for a user. The default key is used for
        situations where the user is not or cannot be asked which API key to
        use.

        :param name: The name of the API key.
        :type name: str
        :param analyst: The user.
        :type analyst: str
        :returns: dict with keys "success" (boolean) and "message" (str).
        """

        c = 0
        for key in self.api_keys:
            if key.name == name:
                self.api_keys[c].default = True
            else:
                self.api_keys[c].default = False
            c += 1
        self.save(username=analyst)
        return {'success': True}

    def revoke_api_key(self, name, analyst):
        """
        Revoke an API key so it can no longer be used.

        :param name: The name of the API key.
        :type name: str
        :param analyst: The user.
        :type analyst: str
        :returns: dict with keys "success" (boolean) and "message" (str).
        """

        keys = self.api_keys
        keyslen = len(keys)
        self.api_keys = [k for k in keys if k.name != name]
        if keyslen > len(self.api_keys):
            self.save(username=analyst)
            return {'success': True}
        else:
            return {'success': False, 'message': 'Key not found.'}

    def get_api_key(self, name):
        """
        Get the API key.

        :param name: The name of the API key.
        :type name: str
        :returns: str, None
        """

        for key in self.api_keys:
            if key.name == name:
                return key.api_key
        return None

    def validate_api_key(self, key):
        """
        Validate that the API key exists for this user.

        :param key: The API key.
        :type key: str
        :returns: True, False
        """

        for keys in self.api_keys:
            if keys.api_key == key:
                return True
        return False

    @classmethod
    def create_user(cls, username, password, email=None, analyst=None):
        """
        Create (and save) a new user with the given username, password and
        email address.
        """

        now = datetime_now()

        # Normalize the address by lowercasing the domain part of the email
        # address.
        if email is not None:
            try:
                email_name, domain_part = email.strip().split('@', 1)
            except ValueError:
                pass
            else:
                email = '@'.join([email_name, domain_part.lower()])

        user = cls(username=username, email=email, date_joined=now)
        user.create_api_key("default", analyst, default=True)
        if password and user.set_password(password):
            user.save(username=analyst)
            return user
        elif CRITsConfig.remote_user:
            user.save(username="CRITS_REMOTE_USER")
            return user
        else:
            return None

    def get_group_permissions(self, obj=None):
        """
        Returns a list of permission strings that this user has through his/her
        groups. This method queries all available auth backends. If an object
        is passed in, only permissions matching this object are returned.
        """
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, "get_group_permissions"):
                permissions.update(backend.get_group_permissions(self, obj))
        return permissions

    def get_all_permissions(self, obj=None):
        return _user_get_all_permissions(self, obj)

    def has_perm(self, perm, obj=None):
        """
        Returns True if the user has the specified permission. This method
        queries all available auth backends, but returns immediately if any
        backend returns True. Thus, a user who has permission from a single
        auth backend is assumed to have permission in general. If an object is
        provided, permissions for this specific object are checked.
        """

        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        # Otherwise we need to check the backends.
        return _user_has_perm(self, perm, obj)

    def has_module_perms(self, app_label):
        """
        Returns True if the user has any permissions in the given app label.
        Uses pretty much the same logic as has_perm, above.
        """
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        return _user_has_module_perms(self, app_label)

    def email_user(self, subject, message, from_email=None):
        """
        Sends an e-mail to this User.
        """

        from django.core.mail import send_mail
        if not from_email:
            crits_config = CRITsConfig.objects().first()
            if crits_config:
                from_email = crits_config.crits_email
        send_mail(subject, message, from_email, [self.email])

    def get_username(self):
        return self.username
    '''
    def get_profile(self):
        """
        Returns site-specific profile for this user. Raises
        SiteProfileNotAvailable if this site does not allow profiles.
        """
        if not hasattr(self, '_profile_cache'):
            from django.conf import settings
            if not getattr(settings, 'AUTH_PROFILE_MODULE', False):
                raise SiteProfileNotAvailable('You need to set AUTH_PROFILE_MO'
                                              'DULE in your project settings')
            try:
                app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
            except ValueError:
                raise SiteProfileNotAvailable('app_label and model_name should'
                        ' be separated by a dot in the AUTH_PROFILE_MODULE set'
                        'ting')

            try:
                model = models.get_model(app_label, model_name)
                if model is None:
                    raise SiteProfileNotAvailable('Unable to load the profile '
                        'model, check AUTH_PROFILE_MODULE in your project sett'
                        'ings')
                self._profile_cache = model._default_manager.using(self._state.db).get(user__id__exact=self.id)
                self._profile_cache.user = self
            except (ImportError, ImproperlyConfigured):
                raise SiteProfileNotAvailable
        return self._profile_cache
    '''
    def get_preference(self, section, setting, default=None):
        """
        Get a user preference setting out of the deep dynamic dictionary
        'section' is the preferences 'section' e.g. 'ui'
        'setting' is the dot separated preference setting  e.g. 'foo.bar.enabled'

        :param section: A specific section of preferences you want.
        :type section: str
        :param setting: The setting you want to get.
        :type setting: str
        :returns: None, str, dict
        """

        if not section in self.prefs:
            return default

        # Split the preference option into subtrees on '.'
        otree = setting.split(".")
        param = otree.pop()
        opt = self.prefs[section]

        if len(otree):
            for subsect in otree:
                if subsect in opt:
                    opt = opt[subsect]
                else:
                    return default

        if not param in opt:
            return default

        return opt[param]

    def update_from_ldap(self, analyst, config=None, passw=''):
        """
        Set First Name, Last Name, and Email from LDAP if we can get the data.
        """

        info = self.info_from_ldap(config, passw)
        if info['result'] == "OK":
            self.first_name = info['first_name']
            self.last_name = info['last_name']
            self.email = info['email']
            self.save(username=analyst)

    def info_from_ldap(self, config=None, password=''):
        """
        Get information about this user from LDAP.
        """

        import ldap, ldapurl
        resp = {"result": "ERROR"}
        if not config:
            config = CRITsConfig.objects().first()
        # Make sure we have the rquired settings, else return failure
        if not config.ldap_server or not config.ldap_userdn:
            return resp
        ldap_server = config.ldap_server.split(':')
        scheme = "ldap"
        if config.ldap_tls:
            scheme = "ldaps"
        url = ldapurl.LDAPUrl('%s://%s' % (scheme, ldap_server[0]))
        if len(ldap_server) == 2:
            l = ldap.initialize('%s:%s' % (url.unparse(),
                                           ldap_server[1]))
        else:
            l = ldap.initialize(url.unparse())
        l.protocol_version = 3
        l.set_option(ldap.OPT_REFERRALS, 0)
        l.set_option(ldap.OPT_TIMEOUT, 10)
        # setup auth for custom cn's
        cn = "cn="
        if config.ldap_usercn:
            cn = config.ldap_usercn
        # two-step ldap binding
        if len(config.ldap_bind_dn) > 0:
            try:
            	logger.info("binding with bind_dn: %s" % config.ldap_bind_dn)
            	l.simple_bind_s(config.ldap_bind_dn, config.ldap_bind_password)
            	filter = '(|(cn='+self.username+')(uid='+self.username+')(mail='+self.username+'))'
            	# use the retrieved dn for the second bind
            	un = l.search_s(config.ldap_userdn,ldap.SCOPE_SUBTREE,filter,['dn'])[0][0]
            except Exception as err:
            	#logger.error("Error binding to LDAP for: %s" % config.ldap_bind_dn)
            	logger.error("Error in info_from_ldap: %s" % err)
            l.unbind()
            if len(ldap_server) == 2:
                l = ldap.initialize('%s:%s' % (url.unparse(),
                                               ldap_server[1]))
            else:
                l = ldap.initialize(url.unparse())
            l.protocol_version = 3
            l.set_option(ldap.OPT_REFERRALS, 0)
            l.set_option(ldap.OPT_TIMEOUT, 10)
        else:
            un = self.username
        # setup auth for custom cn's
        if len(config.ldap_usercn) > 0:
            un = "%s%s,%s" % (config.ldap_usercn,
                              self.username,
                              config.ldap_userdn)
        elif "@" in config.ldap_userdn:
            un = "%s%s" % (self.username, config.ldap_userdn)
	try:
            # Try auth bind first
            l.simple_bind_s(un, password)
            logger.info("Bound to LDAP for: %s" % un)
        except Exception as e:
            #logger.error("Error binding to LDAP for: %s" % self.username)
            logger.error("info_from_ldap:ERR: %s" % e)
        try:
            uatr = None
            uatr = l.search_s(config.ldap_userdn,
                              ldap.SCOPE_SUBTREE,
                              '(|(cn='+self.username+')(uid='+self.username+'))'
                              )[0][1]
            resp['first_name'] = uatr['givenName'][0]
            resp['last_name'] = uatr['sn'][0]
            resp['email'] = uatr['mail'][0]
            resp['result'] = "OK"
            logger.info("Retrieved LDAP info for: %s" % self.username)
        except Exception as e:
            #logger.error("Error retrieving LDAP info for: %s" % self.username)
            logger.error("info_from_ldap ERR: %s" % e)
        l.unbind()
        return resp

    def getDashboards(self):
        from crits.dashboards.handlers import getDashboardsForUser
        return getDashboardsForUser(self)

class AuthenticationMiddleware(object):
    # This has been added to make theSessions work on Django 1.8+ and
    # mongoengine 0.8.8 see:
    # https://github.com/MongoEngine/mongoengine/issues/966

    def _get_user_session_key(self, request):
        from bson.objectid import ObjectId

        # This value in the session is always serialized to a string, so we need
        # to convert it back to Python whenever we access it.
        SESSION_KEY = '_auth_user_id'
        if SESSION_KEY in request.session:
            return ObjectId(request.session[SESSION_KEY])

    def process_request(self, request):
        from django.utils.functional import SimpleLazyObject
        from mongoengine.django.auth import get_user

        assert hasattr(request, 'session'), (
            "The Django authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE_CLASSES setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'django.contrib.auth.middleware.AuthenticationMiddleware'."
        )
        request.user = SimpleLazyObject(lambda: get_user(self._get_user_session_key(request)))

# stolen from MongoEngine and modified to use the CRITsUser class.
class CRITsAuthBackend(object):
    """
    Authenticate using MongoEngine and crits.core.user.CRITsUser.
    """

    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, username=None, password=None, user_agent=None,
                     remote_addr=None, accept_language=None,
                     totp_enabled='Disabled'):
        """
        Perform the authentication of the user.

        :param username: The user to authenticate.
        :type username: str
        :param password: The password provided to authenticate with.
        :type password: str
        :param user_agent: The user-agent in the request.
        :type user_agent: str
        :param remote_addr: The hostname/ip in the request.
        :type remote_addr: str
        :param accept_language: The Accept Language in the request.
        :type accept_language: str
        :param totp_enabled: If TOTP is enabled and should be checked as well.
        :type totp_enabled: str
        :returns: :class:`crits.core.user.CRITsUser`, None
        """

        # Need username and password for logins, checkem both
        if not all([username, password]):
            return None

        e = EmbeddedLoginAttempt()
        e.user_agent = user_agent
        e.remote_addr = remote_addr
        e.accept_language = accept_language
        fusername = username
        if '\\' in username:
            username = username.split("\\")[1]
        user = CRITsUser.objects(username=username).first()
        if user:
            # If the user needs TOTP and it is not disabled system-wide, and
            # the user has exceeded the login threshold for this time period
            # don't go any further. Track the invalid login and return.
            if (((user.totp and totp_enabled == 'Optional') or
                    totp_enabled == 'Required') and
                    self._exceeded_login_threshold(user)):
                e.success = False
                self.track_login_attempt(user, e)
                user.reload()
                return None
            config = CRITsConfig.objects().first()
            if not config:
                return None
            if config.ldap_auth:
                import ldap, ldapurl
                try:
                    # If you are using Oracle's server that's based on
                    # Netscape's code, and your users can't login after
                    # password expiration warning kicks in, you need:
                    # python-ldap 2.4.15 installed and
                    # import ldap.controls.pwdpolicy to fix it
                    #
                    import ldap.controls.pwdpolicy
                except ImportError:
                    logger.info("ldap.controls.pwdpolicy not present.")
                try:
                    # don't parse the port if there is one
                    ldap_server = config.ldap_server.split(':')
                    scheme = "ldap"
                    if config.ldap_tls:
                        scheme = "ldaps"
                    url = ldapurl.LDAPUrl('%s://%s' % (scheme, ldap_server[0]))
                    if len(ldap_server) == 2:
                        l = ldap.initialize('%s:%s' % (url.unparse(),
                                                       ldap_server[1]))
                    else:
                        l = ldap.initialize(url.unparse())
                    l.protocol_version = 3
                    l.set_option(ldap.OPT_REFERRALS, 0)
                    l.set_option(ldap.OPT_TIMEOUT, 10)
                    # two-step ldap binding
                    if len(config.ldap_bind_dn) > 0:
                    	try:
                    		logger.info("binding with bind_dn: %s" % config.ldap_bind_dn)
                    		l.simple_bind_s(config.ldap_bind_dn, config.ldap_bind_password)
                    		filter = '(|(cn='+fusername+')(uid='+fusername+')(mail='+fusername+'))'
                    		# use the retrieved dn for the second bind
                        	un = l.search_s(config.ldap_userdn,ldap.SCOPE_SUBTREE,filter,['dn'])[0][0]
                        except Exception as err:
            			#logger.error("Error binding to LDAP for: %s" % config.ldap_bind_dn)
            			logger.error("authenticate ERR: %s" % err)
                        l.unbind()
                        if len(ldap_server) == 2:
                            l = ldap.initialize('%s:%s' % (url.unparse(),
                                                           ldap_server[1]))
                        else:
                            l = ldap.initialize(url.unparse())
                        l.protocol_version = 3
                        l.set_option(ldap.OPT_REFERRALS, 0)
                        l.set_option(ldap.OPT_TIMEOUT, 10)
                    else:
                        un = fusername
                    # setup auth for custom cn's
                    if len(config.ldap_usercn) > 0:
                        un = "%s%s,%s" % (config.ldap_usercn,
                                          fusername,
                                          config.ldap_userdn)
                    elif "@" in config.ldap_userdn:
                        un = "%s%s" % (fusername, config.ldap_userdn)
                    logger.info("Logging in user: %s" % un)
                    l.simple_bind_s(un, password)
                    user = self._successful_settings(user, e, totp_enabled)
                    if config.ldap_update_on_login:
                        user.update_from_ldap("Auto LDAP update", config, password)
                    l.unbind()
                    return user
                except ldap.INVALID_CREDENTIALS:
                    l.unbind()
                    logger.info("Invalid LDAP credentials for: %s" % un)
                except Exception as err:
                    logger.info("LDAP Auth error: %s" % err)
            # If LDAP auth fails, attempt normal CRITs auth.
            # This will help with being able to use local admin accounts when
            # you have LDAP auth enabled.
            if password and user.check_password(password):
                self._successful_settings(user, e, totp_enabled)
                if config.ldap_update_on_login:
                    user.update_from_ldap("Auto LDAP update", config)
                return user
            else:
                e.success = False
                user.invalid_login_attempts += 1

            if user.is_active and user.invalid_login_attempts > settings.INVALID_LOGIN_ATTEMPTS:
                user.is_active = False
                logger.info("Account disabled due to too many invalid login attempts: %s" %
                            user.username)

                if config.crits_email_end_tag:
                    subject = "CRITs Account Lockout" + config.crits_email_subject_tag
                else:
                    subject = config.crits_email_subject_tag + "CRITs Account Lockout"
                body = """

You are receiving this email because your CRITs account has been locked out due to
too many invalid login attempts.  If you did not perform this action,
someone may be attempting to access your account.

Please contact a site administrator to resolve.

"""
                try:
                    user.email_user(subject, body)
                except Exception, err:
                    logger.warning("Error sending email: %s" % str(err))
            self.track_login_attempt(user, e)
            user.reload()
        return None

    def track_login_attempt(self, user, login_attempt):
        """
        Track this login attempt.
        """

        # only track the last 50 login attempts
        if len(user.login_attempts) > 49:
            user.login_attempts = user.login_attempts[-49:]
        user.login_attempts.append(login_attempt)
        user.save()

    def get_user(self, user_id):
        """
        Get a user with the specified user_id.
        """

        return CRITsUser.objects.with_id(user_id)

    def _exceeded_login_threshold(self, user, interval=10):
        """
        Throttle login attempts for this user so they can't be locked out by a
        brute force attempt. Requires that the user wait 10 seconds before
        another attempt will be attempted.
        """

        # If the user was just created, they may not have an attempt logged
        if not user.login_attempts:
            return False
        # If last login attempt was success, don't bother checking.
        if user.login_attempts[-1].success:
            return False

        ct = time.time()
        try:
            lt = time.mktime(user.login_attempts[-1]['date'].timetuple())
        except:
            lt = 0
        if ct - lt < 10:
            logger.info("Multiple login attempts detected exceeding "
                        "threshold of 10 seconds for user %s" % user.username)
            return True
        return False

    def _successful_settings(self, user, e, totp_enabled):
        """
        Adjust the user document and the request after a successful login.
        """

        # If login requires TOTP, don't log this as a success yet
        if ((user.totp and totp_enabled == 'Optional') or
            totp_enabled == 'Required'):
            return user
        e.success = True
        # only track the last 50 login attempts
        if len(user.login_attempts) > 49:
            user.login_attempts = user.login_attempts[-49:]
        user.login_attempts.append(e)
        user.save()
        backend = auth.get_backends()[0]
        user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
        return user


class CRITsRemoteUserBackend(CRITsAuthBackend):
    """
    Handle CRITs users when dealing with REMOTE_USER
    """

    def authenticate(self, username, password=None, user_agent=None,
                     remote_addr=None, accept_language=None,
                     totp_enabled='Disabled'):
        """
        Perform the authentication of the user.

        :param username: The user to authenticate.
        :type username: str
        :param password: The password provided to authenticate with.
        :type password: str
        :param user_agent: The user-agent in the request.
        :type user_agent: str
        :param remote_addr: The hostname/ip in the request.
        :type remote_addr: str
        :param accept_language: The Accept Language in the request.
        :type accept_language: str
        :param totp_enabled: If TOTP is enabled and should be checked as well.
        :type totp_enabled: str
        :returns: :class:`crits.core.user.CRITsUser`, None
        """

        e = EmbeddedLoginAttempt()
        e.user_agent = user_agent
        e.remote_addr = remote_addr
        e.accept_language = accept_language
        if not username:
            logger.warn("No username passed to CRITsRemoteUserBackend (auth)")
            return None
        config = CRITsConfig.objects().first()
        user = None
        username = self.clean_username(username)
        user = CRITsUser.objects(username=username).first()
        if user and user.is_active:
            if self._exceeded_login_threshold(user):
                return None

            # Log in user
            self._successful_settings(user, e, totp_enabled)
            if config.ldap_update_on_login:
                user.update_from_ldap("Auto LDAP update", config)
            return user
        elif not user and config.create_unknown_user:
            # Create the user
            user = CRITsUser.create_user(username=username, password=None)
            user.sources.append(config.company_name)
            # Attempt to update info from LDAP
            user.update_from_ldap("Auto LDAP update", config)
            user = self._successful_settings(user, e, totp_enabled)
            return user
        else:
            logger.warn("Unknown user and not creating accounts.")
            return None

    def clean_username(self, username):
        """
        Clean the username.
        """

        return username

    def configure_user(self, user):
        """
        Return the user.
        """

        return user
