import copy
import os

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError as CE

from crits.config.config import CRITsConfig

RESET_CONFIG_VARIABLE = "reset_config"
CREATE_CONFIG_VARIABLE = "create_config"
REINSERT_CONFIG_VARIABLE = "reinsert_config"

class Command(BaseCommand):
    """
    Script Class.
    """

    option_list = (
        make_option("--" + RESET_CONFIG_VARIABLE,
                    action='store_true',
                    dest=RESET_CONFIG_VARIABLE,
                    default=False,
                    help='Forces a reset of ALL CRITs configuration ' +
                            'settings by dropping the config collection ' +
                            'and then setting the to default values in the ' +
                            'target DB instance. This has the highest ' +
                            'precedence over other options.'),
        make_option("--" + CREATE_CONFIG_VARIABLE,
                    action='store_true',
                    dest=CREATE_CONFIG_VARIABLE,
                    default=False,
                    help='Creates a new default CRITs config only if there ' +
                            'is no default configuration in the target ' +
                            'DB instance. This has the second highest ' +
                            'precedence over other options.'),
        make_option("--" + REINSERT_CONFIG_VARIABLE,
                    action='store_true',
                    dest=REINSERT_CONFIG_VARIABLE,
                    default=False,
                    help='Copies the old CRITs_config, inserts the copy, ' +
                    'and then deletes the old CRITsConfig ' +
                    'This allows a document to "refresh" or explicitly ' +
                    'write the config fields to the database -- this ' +
                    'is due to the fact that variables are not written to ' +
                    'the database unless a "dirty"/"changed" is set for ' +
                    'fields. This is done for performance reasons. ' +
                    'This could result in missing fields from the ' +
                    'database, even though defaults specified by the ' +
                    'document in Python is correct. This has the third ' +
                    'highest precedence over other options.'),
    ) + BaseCommand.option_list

    args = """<configuration option> <value>

           Available configuration options:

           allowed_hosts:\t\t<list of allowed_hosts>
           classification:\t\t<string> (ex: "unclassified")
           company_name:\t\t<string>
           create_unknown_user:\t\t<boolean> (ex: True, true, yes, or 1)
           crits_message:\t\t<Login screen message string>
           crits_email:\t\t\t<email address string>
           crits_email_subject_tag:\t<string>
           crits_email_end_tag:\t\t<boolean> (ex: True, true, yes, or 1)
           crits_version:\t\t<X.X.X string>
           debug:\t\t\t<boolean> (ex: True, true, yes, or 1)
           depth_max:\t\t\t<integer>
           email_host:\t\t\t<string>
           email_port:\t\t\t<string>
           enable_api:\t\t\t<boolean> (ex: True, true, yes, or 1)
           enable_toasts:\t\t\t<boolean> (ex: True, true, yes, or 1)
           git_repo_url:\t\t<string>
           http_proxy:\t\t\t<string>
           instance_name:\t\t<string>
           instance_url:\t\t<string>
           invalid_login_attempts:\t<integer>
           language_code:\t\t<string> (ex: "en-us")
           ldap_auth:\t\t\t<boolean> (ex: True, true, yes, or 1)
           ldap_tls:\t\t\t<boolean> (ex: True, true, yes, or 1)
           ldap_server:\t\t\t<string>
           ldap_usercn:\t\t\t<string>
           ldap_userdn:\t\t\t<string>
           ldap_update_on_login:\t<boolean> (ex: True, true, yes, or 1)
           log_directory:\t\t<full directory path>
           log_level:\t\t\t<INFO/DEBUG/WARN>
           password_complexity_desc:\t<string>
           password_complexity_regex:\t<string>
           query_caching:\t\t<boolean> (ex: True, true, yes, or 1)
           rel_max:\t\t\t<integer>
           remote_user:\t\t\t<boolean> (ex: True, true, yes, or 1)
           rt_url:\t\t\t<string>
           secure_cookie:\t\t<boolean> (ex: True, true, yes, or 1)
           service_dirs:\t\t<list of full directory paths>
           service_model:\t\t<process/thread/process_pool/thread_pool/local>
           session_timeout:\t\t<integer>
           splunk_search_url:\t\t<string>
           temp_dir:\t\t\t<full directory path>
           timezone:\t\t\t<string> (ex: "America/New_York")
           total_max:\t\t\t<integer>
           totp_cli:\t\t\t<string> (ex: Disabled, Required, Optional)
           totp_web:\t\t\t<string> (ex: Disabled, Required, Optional)
           zip7_path:\t\t\t<full file path>
           zip7_password:\t\t\t<string> (ex: infected)"""
    help = 'Set a CRITs configuration option.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        reset_config_option = options.get(RESET_CONFIG_VARIABLE)
        create_config_option = options.get(CREATE_CONFIG_VARIABLE)
        reinsert_config_option = options.get(REINSERT_CONFIG_VARIABLE)

        if reset_config_option == True:
            force_reset_config();
        if create_config_option == True:
            create_config_if_not_exist();

        if len(args) == 2 or reinsert_config_option == True:
            # Get the config
            crits_config = create_config_if_not_exist();

            if len(args) == 2:
                attr = args[0]
                value = args[1]

                # Check to make sure the attribute is a known attribute
                if set_config_attribute(crits_config, attr, value) == False:
                    raise CE('CRITs has no configuration option %s.' % attr)

            # Save the config to the database
            if reinsert_config_option == True:
                print "Performing a reinsert of the CRITs configuration."
                reinsert_config(crits_config)
            else:
                print "Saving CRITs configuration."
                crits_config.save()

        elif reset_config_option == False and create_config_option == False and reinsert_config_option == False:
            raise CE('setconfig: Invalid Parameters! Only takes two ' +
                     'arguments or --create_config_option or --reset_config_option flags.')

def create_config_if_not_exist():
    """
    If the CRITsConfig already exists then the CRITsConfig is returned,
    otherwise a new CRITsConfig will be created, saved, and returned.

    Returns:
        Returns the CRITsConfig if it already exists, otherwise a
        default CRITsConfig is returned.
    """

    crits_config = CRITsConfig.objects().first()
    if not crits_config:
        print "Creating a new CRITs configuration."
        crits_config = CRITsConfig()
        crits_config.save()
    else:
        print "A CRITs configuration already exists. Skipping default creation."

    return crits_config

def reinsert_config(old_config):
    """
    Copies old_config, inserts the copy, and then deletes the old CRITsConfig

    This allows a document to "refresh" or explicitly write the config fields to
    the database -- this is due to the fact that variables are not written to
    the database unless a "dirty"/"changed" is set for fields. This is done
    for performance reasons. This could result in missing fields from the
    database, even though defaults specified by the document in Python is
    correct.

    Args:
        crits_config: The CRITsConfig to copy, insert and delete
    """

    new_config = copy.deepcopy(old_config)
    new_config.id = None
    new_config.save()
    old_config.delete()

def force_reset_config():
    """
    Resets the values for the CRITsConfig class by dropping the
    database collection and then saving a new default CRITsConfig.
    """

    print "Resetting CRITs configuration settings."
    CRITsConfig.drop_collection();

    crits_config = CRITsConfig();
    crits_config.save();

def set_config_attribute(crits_config, attr, value):
    """
    Sets the value for the attribute for the input CRITsConfig. If the
    attribute doesn't exist then nothing happens.

    Args:
        crits_config: The CRITsConfig to copy
        attr: The attribute to set
        value: The value to set for the input attribute

    Returns:
        Returns true if the attribute was able to be set. False otherwise.
    """

    is_successful = False;

    if hasattr(crits_config, attr):
        if attr in ("enable_api", "create_unknown_user", "debug", "ldap_auth",
                    "ldap_tls", "remote_user", "secure_cookie", "enable_toasts",
                    "ldap_update_on_login", "query_caching",
                    "crits_email_end_tag"):
            if value in ('True', 'true', 'yes', '1'):
                value = True
            elif value in ('False', 'false', 'no', '0'):
                value = False
            else:
                raise CE('%s is a boolean True/False.' % attr)
        if attr in ('depth_max', 'invalid_login_attempts', 'rel_max',
                    'session_timeout', 'service_pool_size', 'total_max'):
            try:
                value = int(value)
            except:
                raise CE('%s is an Integer' % attr)
        if attr == "log_level":
            if not value in ('INFO', 'WARN', 'DEBUG'):
                raise CE('log_level must be INFO, WARN, or DEBUG.')
        if attr in ('temp_dir', 'zip7_path', 'log_directory'):
            if not os.path.exists(value):
                raise CE('Not a valid path: %s' % value)
        if attr == "allowed_hosts":
            li = value.split(',')
            value = [l.strip() for l in li]
        if attr == "service_dirs":
            li = value.split(',')
            value = [l.strip() for l in li]
            for v in value:
                if not os.path.exists(v):
                    raise CE('Not a valid path: %s' % v)
        if attr == "service_model":
            if value not in ('process', 'thread', 'process_pool', 'thread_pool', 'local'):
                raise CE('service_model must be process, thread, process_pool, thread_pool, or local')
        if attr in ('totp_web', 'totp_cli'):
            if value not in ('Optional', 'Disabled', 'Required'):
                raise CE('totp_web/cli must be Optional, Required, or Disabled')

        print "Setting [" + str(attr) + "] to a value of [" + str(value) + "]"
        setattr(crits_config, attr, value)

        is_successful = True

    return is_successful
