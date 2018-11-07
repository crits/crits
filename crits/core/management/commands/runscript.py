import getpass
import os
import socket

from crits.settings import crits_config
from django.core.management.base import BaseCommand, CommandError
from crits.core.user import CRITsUser


from crits.core.handlers import login_user
from crits.vocabulary.acls import GeneralACL

class Command(BaseCommand):
    """
    Script Class.
    """
    def add_arguments(self, parser):
        parser.add_argument("-e", "--environ-auth", action="store_true", dest='environ',
                        default=False,
                        help=("Authenticate using 'CRITS_USER' and 'CRITS_PASSWORD'"
                              " environment variables (overrides -u and -p)."))
        parser.add_argument("-u", "--username", dest='username', default=None,
                        help="Username to log in with (will prompt if not provided).")
        parser.add_argument("-p", "--password", dest='password', default=None,
                        help="Password to log in with (will prompt if not provided).")
        parser.add_argument('args', nargs='*')
        args = '<location> <script> -- <script argument 1> ...'
        help = ('Runs scripts using the CRITs environment.\n'
                '<location>:\t"crits_scripts" (without quotes) to run a CRITs script '
                '\n\t\tor "foo" (without quotes) where foo is the name of a service.\n'
                '<script>:\tthe name of the script to run.\n')

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        if len(args) < 2:
            raise CommandError(('Not enough arguments specified (see -h).'))

        class_name = 'CRITsScript'
        try:
            tmp_ = __import__('%s.scripts.%s' % (args[0], args[1]),
                              globals(),
                              locals(),
                              ['class_name'],
                              -1)
            script_class = getattr(tmp_, class_name)
        except Exception, e:
            raise CommandError('%s' % e)

        arg_list = []
        if len(args) > 2:
            arg_list = list(args)[2:]

        # authenticate user with CRITs
        if options.get('environ'):
            username = os.environ.get('CRITS_USER', None)
            password = os.environ.get('CRITS_PASSWORD', None)
        else:
            username = options.get('username')
            password = options.get('password')
        if not username:
            username = getpass.getpass("Username: ")
        if not password:
            password = getpass.getpass("Password: ")

        # see if user exists for totp check
        u = CRITsUser.objects(username=username).first()
        totp_pass = None
        if u:
            totp_enabled = crits_config.get('totp_cli', 'Disabled')
            if (totp_enabled == 'Required' or
                (u.totp and totp_enabled == 'Optional')):
                print ("TOTP is enabled. If you are setting up TOTP for the "
                       "first time, enter a PIN only.")
                totp_pass = getpass.getpass("TOTP: ")

        user_agent = "CRITs %s runscript: %s/%s by %s" % (crits_config['crits_version'],
                                                          args[0], args[1],
                                                          getpass.getuser())
        remote_addr = socket.gethostname()
        accept_language = os.environ.get('LANG', "Unknown")

        try_login(username, password, user_agent=user_agent,
                  remote_addr=remote_addr, accept_language=accept_language,
                  totp_pass=totp_pass)

        if u.has_access_to(GeneralACL.SCRIPT_INTERFACE):
            script = script_class(user=u)
            script.run(arg_list)
        else:
            raise CommandError(('User does not have permission to run CRITs Scripts.'))


def try_login(username, password, user_agent, remote_addr, accept_language,
              totp_pass=None):
    """
    Attempt to authenticate the user running the script.

    :param username: Username to authenticate.
    :type username: str
    :param password: Password to authenticate with.
    :type password: str
    :param user_agent: Information about what script is being executed.
    :type user_agent: str
    :param remote_addr: The address/hostname of the host the script is being run
                        on.
    :type remote_addr: str
    :param accept_language: The 'LANG' environment variable if available.
    :type accept_language: str
    :param totp_pass: The TOTP password if provided.
    :type totp_pass: str
    :returns: :class:`django.core.management.base.CommandError` if failed.
    """

    result = login_user(username,
                        password,
                        next_url=None,
                        user_agent=user_agent,
                        remote_addr=remote_addr,
                        accept_language=accept_language,
                        totp_pass=totp_pass)

    if not result['success']:
        if result['type'] == "no_secret":
            totp_pass = getpass.getpass("Enter New TOTP Pin: ")
            try_login(username, password, user_agent, remote_addr,
                        accept_language, totp_pass)
        if result['type'] == "secret_generated":
            print "Use %s to setup your authenticator.\n" % result['secret']
            totp_pass = getpass.getpass("TOTP: ")
            try_login(username, password, user_agent, remote_addr,
                        accept_language, totp_pass)
        if result['type'] == "login_failed":
            raise CommandError(('Login failed: %s' % result['message']))

    return
