# CRITs environment chooser

import errno
import glob
import os
import sys
import django
import subprocess

from pymongo import ReadPreference, MongoClient
from mongoengine import connect

sys.path.insert(0, os.path.dirname(__file__))

# calculated paths for django and the site
# used as starting points for various other paths
DJANGO_ROOT = os.path.dirname(os.path.realpath(django.__file__))
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

TEST_RUNNER = 'django.test.runner.DiscoverRunner'
# Version
CRITS_VERSION = '4-master'

#the following gets the current git hash to be displayed in the footer and
#hides it if it is not a git repo
try:
    HIDE_GIT_HASH = False
    #get the short hand of current git hash
    GIT_HASH = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=SITE_ROOT).strip()
    #get the long hand of the current git hash
    GIT_HASH_LONG = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SITE_ROOT).strip()
    #get the git branch
    GIT_BRANCH = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=SITE_ROOT).strip()
except:
    #if it is not a git repo, clear out all values and hide them
    GIT_HASH = ''
    GIT_HASH_LONG = ''
    HIDE_GIT_HASH = True
    GIT_BRANCH = ''

APPEND_SLASH = True
TEST_RUN = False

# Set to DENY|SAMEORIGIN|ALLOW-FROM uri
# Default: SAMEORIGIN
# More details: https://developer.mozilla.org/en-US/docs/HTTP/X-Frame-Options
#X_FRAME_OPTIONS = 'ALLOW-FROM https://www.example.com'

# Setup for runserver or Apache
if 'runserver' in sys.argv:
    DEVEL_INSTANCE = True
    SERVICE_MODEL = 'thread'
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    LOGIN_URL = "/login/"
elif 'test' in sys.argv:
    TEST_RUN = True
    DEVEL_INSTANCE = True
    SERVICE_MODEL = 'thread'
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    LOGIN_URL = "/login/"
else:
    DEVEL_INSTANCE = False
    SERVICE_MODEL = 'process'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    LOGIN_URL = "/login/"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy'
    }
}


# MongoDB Default Configuration
# Tip: To change database settings, override by using
#      template from config/database_example.py
MONGO_HOST = 'localhost'                          # server to connect to
MONGO_PORT = 27017                                # port MongoD is running on
MONGO_DATABASE = 'crits'                          # database name to connect to
MONGO_SSL = False                                 # whether MongoD has SSL enabled
MONGO_USER = ''                                   # username used to authenticate to mongo (normally empty)
MONGO_PASSWORD = ''                               # password for the mongo user

# File storage backends
S3 = "S3"
GRIDFS = "GRIDFS"

# DB to use for files
FILE_DB = GRIDFS

# S3 buckets
BUCKET_PCAPS = "pcaps"
BUCKET_OBJECTS = "objects"
BUCKET_SAMPLES = "samples"

# Import custom Database config
dbfile = os.path.join(SITE_ROOT, 'config/database.py')
if os.path.exists(dbfile):
    execfile(dbfile)

if TEST_RUN:
    MONGO_DATABASE = 'crits-unittest'

# Read preference to configure which nodes you can read from
# Possible values:
# primary: queries are sent to the primary node in a replicSet
# secondary: queries are allowed if sent to primary or secondary
#            (for single host) or are distributed to secondaries
#            if you are connecting through a router
# More info can be found here:
# http://api.mongodb.org/python/current/api/pymongo/index.html
MONGO_READ_PREFERENCE = ReadPreference.PRIMARY


# MongoDB default collections
COL_ACTORS = "actors"                                     # main collection for actors
COL_ACTOR_IDENTIFIERS = "actor_identifiers"               # main collection for actor identifiers
COL_ACTOR_THREAT_IDENTIFIERS = "actor_threat_identifiers" # actor threat identifiers
COL_ACTOR_THREAT_TYPES = "actor_threat_types"             # actor threat types
COL_ACTOR_MOTIVATIONS = "actor_motivations"               # actor motivations
COL_ACTOR_SOPHISTICATIONS = "actor_sophistications"       # actor sophistications
COL_ACTOR_INTENDED_EFFECTS = "actor_intended_effects"     # actor intended effects
COL_ANALYSIS_RESULTS = "analysis_results"                 # analysis results
COL_AUDIT_LOG = "audit_log"                               # audit log entries
COL_BACKDOORS = "backdoors"                               # backdoors
COL_BUCKET_LISTS = "bucket_lists"                         # bucketlist information
COL_CAMPAIGNS = "campaigns"                               # campaigns list
COL_CERTIFICATES = "certificates"                         # certificates list
COL_COMMENTS = "comments"                                 # comments collection
COL_CONFIG = "config"                                     # config collection
COL_COUNTS = "counts"                                     # general counts for dashboard
COL_DIVISION_DATA = "division_data"                       # information on divisions within company
COL_DOMAINS = "domains"                                   # root domains with FQDNs and IP information
COL_EFFECTIVE_TLDS = "effective_tlds"                     # list of effective TLDs from Mozilla to determine root domains
COL_EMAIL = "email"                                       # main email collection
COL_EVENTS = "events"                                     # main events collection
COL_EVENT_TYPES = "event_types"                           # event types for events
COL_EXPLOITS = "exploits"                                 # exploits
COL_FILETYPES = "filetypes"                               # list of filetypes in system generated by MapReduce
COL_IDB_ACTIONS = "idb_actions"                           # list of available actions to be taken with indicators
COL_INDICATORS = "indicators"                             # main indicators collection
COL_INTERNAL_LOCATIONS = "internal_locations"             # site locations for company
COL_IPS = "ips"                                           # IPs collection
COL_LOCATIONS = "locations"                               # Locations collection
COL_NOTIFICATIONS = "notifications"                       # notifications collection
COL_OBJECTS = "objects"                                   # objects that are files that have been added
COL_OBJECT_TYPES = "object_types"                         # types of objects that can be added
COL_PCAPS = "pcaps"                                       # main pcaps collection
COL_RAW_DATA = "raw_data"                                 # main raw data collection
COL_RAW_DATA_TYPES = "raw_data_types"                     # list of available raw data types
COL_RELATIONSHIP_TYPES = "relationship_types"             # list of available relationship types
COL_SAMPLES = "sample"                                    # main samples collection
COL_SCREENSHOTS = "screenshots"                           # main screenshots collection
COL_SECTOR_LISTS = "sector_lists"                         # sector lists information
COL_SECTORS = "sectors"                                   # available sectors
COL_SERVICES = "services"                                 # list of services for scanning
COL_SIGNATURES = "signatures"                             # main signature collection
COL_SIGNATURE_TYPES = "signature_types"                   # list of available signature types
COL_SIGNATURE_DEPENDENCY = "signature_dependency"	  # list of available signature dependencies
COL_SOURCE_ACCESS = "source_access"                       # source access ACL collection
COL_SOURCES = "sources"                                   # source information generated by MapReduce
COL_STATISTICS = "statistics"                             # list of statistics for different objects (campaigns, for example)
COL_TARGETS = "targets"                                   # target information for use in email
COL_USERS = "users"                                       # main users collection
COL_USER_ROLES = "user_roles"                             # main user roles collection
COL_YARAHITS = "yarahits"                                 # yara hit counts for samples

# MongoDB connection pool
if MONGO_USER:
    connect(MONGO_DATABASE, host=MONGO_HOST, port=MONGO_PORT, read_preference=MONGO_READ_PREFERENCE, ssl=MONGO_SSL,
            username=MONGO_USER, password=MONGO_PASSWORD)
else:
    connect(MONGO_DATABASE, host=MONGO_HOST, port=MONGO_PORT, read_preference=MONGO_READ_PREFERENCE, ssl=MONGO_SSL)

# Get config from DB
c = MongoClient(MONGO_HOST, MONGO_PORT, ssl=MONGO_SSL)
db = c[MONGO_DATABASE]
if MONGO_USER:
    db.authenticate(MONGO_USER, MONGO_PASSWORD)
coll = db[COL_CONFIG]
crits_config = coll.find_one({})
if not crits_config:
    crits_config = {}

# Populate settings
# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
# NOTE: we are setting ALLOWED_HOSTS to ['*'] by default which will work
#       everywhere but is insecure for production installations (no less secure
#       than setting DEBUG to True). This is done because we can't anticipate
#       the host header for every CRITs install and this should work "out of
#       the box".
ALLOWED_HOSTS =             crits_config.get('allowed_hosts', ['*'])
COMPANY_NAME =              crits_config.get('company_name', 'My Company')
CLASSIFICATION =            crits_config.get('classification', 'unclassified')
CRITS_EMAIL =               crits_config.get('crits_email', '')
CRITS_EMAIL_SUBJECT_TAG =   crits_config.get('crits_email_subject_tag', '')
CRITS_EMAIL_END_TAG =       crits_config.get('crits_email_end_tag', True)
DEBUG =                     crits_config.get('debug', True)
if crits_config.get('email_host', None):
    EMAIL_HOST =            crits_config.get('email_host', None)
if crits_config.get('email_port', None):
    EMAIL_PORT =        int(crits_config.get('email_port', None))
ENABLE_API =                crits_config.get('enable_api', False)
ENABLE_TOASTS =             crits_config.get('enable_toasts', False)
GIT_REPO_URL =              crits_config.get('git_repo_url', '')
HTTP_PROXY =                crits_config.get('http_proxy', None)
INSTANCE_NAME =             crits_config.get('instance_name', 'My Instance')
INSTANCE_URL =              crits_config.get('instance_url', '')
INVALID_LOGIN_ATTEMPTS =    crits_config.get('invalid_login_attempts', 3) - 1
LANGUAGE_CODE =             crits_config.get('language_code', 'en-us')
LDAP_AUTH =                 crits_config.get('ldap_auth', False)
LDAP_SERVER =               crits_config.get('ldap_server', '')
LDAP_USERDN =               crits_config.get('ldap_userdn', '')
LDAP_USERCN =               crits_config.get('ldap_usercn', '')
LOG_DIRECTORY =             crits_config.get('log_directory', os.path.join(SITE_ROOT, '..', 'logs'))
LOG_LEVEL =                 crits_config.get('log_level', 'INFO')
QUERY_CACHING =             crits_config.get('query_caching', False)
RT_URL =                    crits_config.get('rt_url', None)
SECURE_COOKIE =             crits_config.get('secure_cookie', True)
SERVICE_DIRS =        tuple(crits_config.get('service_dirs', []))
SERVICE_MODEL =             crits_config.get('service_model', SERVICE_MODEL)
SERVICE_POOL_SIZE =     int(crits_config.get('service_pool_size', 12))
SESSION_TIMEOUT =       int(crits_config.get('session_timeout', 12)) * 60 * 60
SPLUNK_SEARCH_URL =         crits_config.get('splunk_search_url', None)
TEMP_DIR =                  crits_config.get('temp_dir', '/tmp')
TIME_ZONE =                 crits_config.get('timezone', 'America/New_York')
ZIP7_PATH =                 crits_config.get('zip7_path', '/usr/bin/7z')
ZIP7_PASSWORD =             crits_config.get('zip7_password', 'infected')
REMOTE_USER =               crits_config.get('remote_user', False)
PASSWORD_COMPLEXITY_REGEX = crits_config.get('password_complexity_regex', '(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$')
PASSWORD_COMPLEXITY_DESC =  crits_config.get('password_complexity_desc', '8 characters, at least 1 capital, 1 lowercase and 1 number/special')
DEPTH_MAX =                 crits_config.get('depth_max', '10')
TOTAL_MAX =                 crits_config.get('total_max', '250')
REL_MAX =                   crits_config.get('rel_max', '50')
TOTP =                      crits_config.get('totp', False)


COLLECTION_TO_BUCKET_MAPPING = {
    COL_PCAPS: BUCKET_PCAPS,
    COL_OBJECTS: BUCKET_OBJECTS,
    COL_SAMPLES: BUCKET_SAMPLES
}

# check Log Directory
if not os.path.exists(LOG_DIRECTORY):
    LOG_DIRECTORY = os.path.join(SITE_ROOT, '..', 'logs')

# Custom settings for Django
_TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# DATE and DATETIME Formats
DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i:s.u'
PY_DATE_FORMAT = '%Y-%m-%d'
PY_TIME_FORMAT = '%H:%M:%S.%f'
PY_DATETIME_FORMAT = ' '.join([PY_DATE_FORMAT, PY_TIME_FORMAT])
OLD_PY_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
PY_FORM_DATETIME_FORMATS = [PY_DATETIME_FORMAT, OLD_PY_DATETIME_FORMAT]

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(SITE_ROOT, '../extras/www')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/'

STATIC_ROOT = os.path.join(SITE_ROOT, '../extras/www/static')
STATIC_URL = '/static/'

# List of callables that know how to import templates from various sources.
_TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #'django.template.loaders.eggs.load_template_source',
]

#CACHES = {
#    'default': {
#        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#        'LOCATION': 'unix:/data/memcached.sock',
#    }
#}

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'crits.core.user.AuthenticationMiddleware',
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

_TEMPLATE_CONTEXT_PROCESSORS = [
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'crits.core.views.base_context',
    'crits.core.views.collections',
    'crits.core.views.user_context',
]

ROOT_URLCONF = 'crits.urls'

_TEMPLATE_DIRS = [
    os.path.join(SITE_ROOT, '../documentation'),
    os.path.join(SITE_ROOT, 'core/templates'),
    os.path.join(SITE_ROOT, 'actors/templates'),
    os.path.join(SITE_ROOT, 'backdoors/templates'),
    os.path.join(SITE_ROOT, 'core/dashboard/templates'),
    os.path.join(SITE_ROOT, 'campaigns/templates'),
    os.path.join(SITE_ROOT, 'certificates/templates'),
    os.path.join(SITE_ROOT, 'comments/templates'),
    os.path.join(SITE_ROOT, 'config/templates'),
    os.path.join(SITE_ROOT, 'domains/templates'),
    os.path.join(SITE_ROOT, 'emails/templates'),
    os.path.join(SITE_ROOT, 'events/templates'),
    os.path.join(SITE_ROOT, 'exploits/templates'),
    os.path.join(SITE_ROOT, 'indicators/templates'),
    os.path.join(SITE_ROOT, 'ips/templates'),
    os.path.join(SITE_ROOT, 'locations/templates'),
    os.path.join(SITE_ROOT, 'objects/templates'),
    os.path.join(SITE_ROOT, 'pcaps/templates'),
    os.path.join(SITE_ROOT, 'raw_data/templates'),
    os.path.join(SITE_ROOT, 'relationships/templates'),
    os.path.join(SITE_ROOT, 'samples/templates'),
    os.path.join(SITE_ROOT, 'screenshots/templates'),
    os.path.join(SITE_ROOT, 'services/templates'),
    os.path.join(SITE_ROOT, 'signatures/templates'),
    os.path.join(SITE_ROOT, 'stats/templates'),
    os.path.join(SITE_ROOT, 'targets/templates'),
    os.path.join(SITE_ROOT, 'core/templates/dialogs'),
    os.path.join(SITE_ROOT, 'campaigns/templates/dialogs'),
    os.path.join(SITE_ROOT, 'comments/templates/dialogs'),
    os.path.join(SITE_ROOT, 'locations/templates/dialogs'),
    os.path.join(SITE_ROOT, 'objects/templates/dialogs'),
    os.path.join(SITE_ROOT, 'raw_data/templates/dialogs'),
    os.path.join(SITE_ROOT, 'relationships/templates/dialogs'),
    os.path.join(SITE_ROOT, 'screenshots/templates/dialogs'),
    os.path.join(SITE_ROOT, 'signatures/templates/dialogs'),
]


STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, 'core/static'),
    os.path.join(SITE_ROOT, 'actors/static'),
    os.path.join(SITE_ROOT, 'backdoors/static'),
    os.path.join(SITE_ROOT, 'dashboards/static'),
    os.path.join(SITE_ROOT, 'campaigns/static'),
    os.path.join(SITE_ROOT, 'certificates/static'),
    os.path.join(SITE_ROOT, 'comments/static'),
    os.path.join(SITE_ROOT, 'domains/static'),
    os.path.join(SITE_ROOT, 'emails/static'),
    os.path.join(SITE_ROOT, 'events/static'),
    os.path.join(SITE_ROOT, 'exploits/static'),
    os.path.join(SITE_ROOT, 'indicators/static'),
    os.path.join(SITE_ROOT, 'ips/static'),
    os.path.join(SITE_ROOT, 'locations/static'),
    os.path.join(SITE_ROOT, 'objects/static'),
    os.path.join(SITE_ROOT, 'pcaps/static'),
    os.path.join(SITE_ROOT, 'raw_data/static'),
    os.path.join(SITE_ROOT, 'relationships/static'),
    os.path.join(SITE_ROOT, 'samples/static'),
    os.path.join(SITE_ROOT, 'screenshots/static'),
    os.path.join(SITE_ROOT, 'services/static'),
    os.path.join(SITE_ROOT, 'signatures/static'),
    os.path.join(SITE_ROOT, 'config/static'),
    os.path.join(SITE_ROOT, 'targets/static'),
)

INSTALLED_APPS = (
    'crits.core',
    'crits.dashboards',
    'django.contrib.auth',
    'mongoengine.django.mongo_auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'crits.actors',
    'crits.campaigns',
    'crits.certificates',
    'crits.domains',
    'crits.emails',
    'crits.events',
    'crits.indicators',
    'crits.ips',
    'crits.locations',
    'crits.objects',
    'crits.pcaps',
    'crits.raw_data',
    'crits.relationships',
    'crits.samples',
    'crits.screenshots',
    'crits.services',
    'crits.signatures',
    'crits.stats',
    'crits.targets',
    'tastypie',
    'tastypie_mongoengine',
)


AUTH_USER_MODEL = 'mongo_auth.MongoUser'
MONGOENGINE_USER_DOCUMENT = 'crits.core.user.CRITsUser'

SESSION_ENGINE = 'mongoengine.django.sessions'
SESSION_SERIALIZER = 'mongoengine.django.sessions.BSONSerializer'

AUTHENTICATION_BACKENDS = (
    'crits.core.user.CRITsAuthBackend',
)
if REMOTE_USER:
    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'crits.core.user.AuthenticationMiddleware',
        'django.contrib.auth.middleware.RemoteUserMiddleware',
    )
    AUTHENTICATION_BACKENDS = (
        'crits.core.user.CRITsRemoteUserBackend',
    )

MONGODB_DATABASES = {
    "default": {
        "name": 'crits',
        "host": '127.0.0.1',
        "password": None,
        "username": None,
        "tz_aware": True, # if you using timezones in django (USE_TZ = True)
    },
}

# Handle logging after all custom configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': "%(levelname)s %(asctime)s %(name)s %(message)s"
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'normal': {
            'level': LOG_LEVEL,
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(LOG_DIRECTORY, 'crits.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'crits': {
            'handlers': ['normal'],
            'propagate': True,
            'level': 'DEBUG',
        },
    },
}

# Handle creating log directories if they do not exist
for handler in LOGGING['handlers'].values():
    log_file = handler.get('filename')
    if log_file:
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)

            except OSError as e:
                # If file exists
                if e.args[0] == errno.EEXIST:
                    pass
                # re-raise on error that is not
                # easy to automatically handle, such
                # as permission errors
                else:
                    raise

# CRITs Types
CRITS_TYPES = {
    'Actor': COL_ACTORS,
    'AnalysisResult': COL_ANALYSIS_RESULTS,
    'Backdoor': COL_BACKDOORS,
    'Campaign': COL_CAMPAIGNS,
    'Certificate': COL_CERTIFICATES,
    'Comment': COL_COMMENTS,
    'Domain': COL_DOMAINS,
    'Email': COL_EMAIL,
    'Event': COL_EVENTS,
    'Exploit': COL_EXPLOITS,
    'Indicator': COL_INDICATORS,
    'IP': COL_IPS,
    'Notification': COL_NOTIFICATIONS,
    'PCAP': COL_PCAPS,
    'RawData': COL_RAW_DATA,
    'Sample': COL_SAMPLES,
    'Screenshot': COL_SCREENSHOTS,
    'Signature': COL_SIGNATURES,
    'Target': COL_TARGETS,
}


# Custom template lists for loading in different places in the UI
SERVICE_NAV_TEMPLATES = ()
SERVICE_CP_TEMPLATES = ()
SERVICE_TAB_TEMPLATES = ()

# discover services
for service_directory in SERVICE_DIRS:
    if os.path.isdir(service_directory):
        sys.path.insert(0, service_directory)
        for d in os.listdir(service_directory):
            abs_path = os.path.join(service_directory, d, 'templates')
            if os.path.isdir(abs_path):
                _TEMPLATE_DIRS += (abs_path,)
                nav_items = os.path.join(abs_path, '%s_nav_items.html' % d)
                cp_items = os.path.join(abs_path, '%s_cp_items.html' % d)
                view_items = os.path.join(service_directory, d, 'views.py')
                if os.path.isfile(nav_items):
                    SERVICE_NAV_TEMPLATES = SERVICE_NAV_TEMPLATES + ('%s_nav_items.html' % d,)
                if os.path.isfile(cp_items):
                    SERVICE_CP_TEMPLATES = SERVICE_CP_TEMPLATES + ('%s_cp_items.html' % d,)
                if os.path.isfile(view_items):
                    if '%s_context' % d in open(view_items).read():
                        context_module = '%s.views.%s_context' % (d, d)
                        _TEMPLATE_CONTEXT_PROCESSORS += (context_module,)
                for tab_temp in glob.glob('%s/*_tab.html' % abs_path):
                    head, tail = os.path.split(tab_temp)
                    ctype = tail.split('_')[-2]
                    name = "_".join(tail.split('_')[:-2])
                    SERVICE_TAB_TEMPLATES = SERVICE_TAB_TEMPLATES + ((ctype, name, tail),)

# Allow configuration of the META or HEADER variable is used to find
# remote username when REMOTE_USER is enabled.
REMOTE_USER_META = 'REMOTE_USER'

# The next example could be used for reverse proxy setups
# where your frontend might pass Remote-User: header.
#
# WARNING: If you enable this, be 100% certain your backend is not
# directly accessible and this header could be spoofed by an attacker.
#
# REMOTE_USER_META = 'HTTP_REMOTE_USER'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        #'APP_DIRS': False,'
        'DIRS': _TEMPLATE_DIRS,

        'OPTIONS': {

            #'dirs' : #_TEMPLATE_DIRS,
            'context_processors' : _TEMPLATE_CONTEXT_PROCESSORS,
            'debug' : _TEMPLATE_DEBUG,
            'loaders' : _TEMPLATE_LOADERS,

        },
    },
]
django_version = django.get_version()
from distutils.version import StrictVersion
if StrictVersion(django_version) < StrictVersion('1.8.0'):
    TEMPLATE_DEBUG = _TEMPLATE_DEBUG
    TEMPLATE_DIRS = _TEMPLATE_DIRS
    TEMPLATE_CONTEXT_PROCESSORS = _TEMPLATE_CONTEXT_PROCESSORS

# Import custom settings if it exists
csfile = os.path.join(SITE_ROOT, 'config/overrides.py')
if os.path.exists(csfile):
    execfile(csfile)
