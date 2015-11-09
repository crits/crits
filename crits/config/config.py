import os

from mongoengine import Document, StringField, ListField
from mongoengine import BooleanField, IntField

from crits.core.crits_mongoengine import CritsDocument

class CRITsConfig(CritsDocument, Document):
    """
    CRITs Configuration Class.
    """

    from django.conf import settings

    meta = {
        "collection": settings.COL_CONFIG,
        "crits_type": 'Config',
        "latest_schema_version": 1,
        "schema_doc": {
        },
    }

    allowed_hosts = ListField(StringField(), default=['*'])
    classification = StringField(default='unclassified')
    company_name = StringField(default='My Company')
    create_unknown_user = BooleanField(default=False)
    crits_message = StringField(default='')
    crits_email = StringField(default='')
    crits_email_subject_tag = StringField(default='')
    crits_email_end_tag = BooleanField(default=True)
    # This is actually the internal DB version, but is named crits_version
    # for historical reasons.
    crits_version = StringField(required=True,
                                default=settings.CRITS_VERSION)
    debug = BooleanField(default=True)
    depth_max = IntField(default=10)
    email_host = StringField(default='')
    email_port = StringField(default='')
    enable_api = BooleanField(default=False)
    enable_toasts = BooleanField(default=False)
    git_repo_url = StringField(default='https://github.com/crits/crits')
    http_proxy = StringField(default='')
    instance_name = StringField(default='My Instance')
    instance_url = StringField(default='')
    invalid_login_attempts = IntField(default=3)
    language_code = StringField(default='en-us')
    ldap_auth = BooleanField(default=False)
    ldap_tls = BooleanField(default=False)
    ldap_server = StringField(default='')
    ldap_usercn = StringField(default='')
    ldap_userdn = StringField(default='')
    ldap_update_on_login = BooleanField(default=False)
    log_directory = StringField(default=os.path.join(settings.SITE_ROOT, '..', 'logs'))
    log_level = StringField(default='INFO')
    password_complexity_desc = StringField(default='8 characters, at least 1 capital, 1 lowercase and 1 number/special')
    password_complexity_regex = StringField(default='(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$')
    query_caching = BooleanField(default=False)
    rel_max = IntField(default=50)
    remote_user = BooleanField(default=False)
    rt_url = StringField(default='')
    secure_cookie = BooleanField(default=True)
    service_dirs = ListField(StringField())
    service_model = StringField(default='process')
    service_pool_size = IntField(default=12)
    session_timeout = IntField(default=12)
    splunk_search_url = StringField(default='')
    temp_dir = StringField(default='/tmp')
    timezone = StringField(default='America/New_York')
    total_max = IntField(default=250)
    totp_web = StringField(default='Disabled')
    totp_cli = StringField(default='Disabled')
    zip7_path = StringField(default='/usr/bin/7z')
    zip7_password = StringField(default='infected')

    def migrate(self):
        """
        Migrate the Configuration Schema to the latest version.
        """

        pass
