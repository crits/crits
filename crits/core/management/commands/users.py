import string
import re

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from random import choice

from crits.core.user import CRITsUser
from crits.config.config import CRITsConfig
import settings

class Command(BaseCommand):
    """
    Script Class.
    """

    option_list = BaseCommand.option_list + (
        make_option('--adduser',
                    '-a',
                    dest='adduser',
                    action='store_true',
                    default=False,
                    help='Add a new user to CRITs.'),
        make_option('--administrator',
                    '-A',
                    dest='admin',
                    action='store_true',
                    default=False,
                    help='Make this user an administrator.'),
        make_option('--clearsecret',
                    '-c',
                    dest='clearsecret',
                    action='store_true',
                    default=False,
                    help="Clear a user's secret."),
        make_option('--deactivateuser',
                    '-d',
                    dest='deactivate',
                    action='store_true',
                    default=False,
                    help='Deactivate a user account.'),
        make_option('--email',
                    '-e',
                    dest='email',
                    default=None,
                    help='Email address of new user.'),
        make_option('--sendemail',
                    '-E',
                    dest='sendemail',
                    action='store_true',
                    default=False,
                    help='Email new user their temporary password.'),
        make_option('--firstname',
                    '-f',
                    dest='firstname',
                    default='',
                    help='First name of new user.'),
        make_option('--invalidreset',
                    '-i',
                    dest='invalidreset',
                    action='store_true',
                    default=False,
                    help="Reset a user's invalid login attempts to 0."),
        make_option('--lastname',
                    '-l',
                    dest='lastname',
                    default='',
                    help='Last name of new user.'),
        make_option('--organization',
                    '-o',
                    dest='organization',
                    default='',
                    help='Assign user to an organization/source.'),
        make_option('--password',
                    '-p',
                    dest='password',
                    default='',
                    help='Specify a password for the account.'),
        make_option('--reset',
                    '-r',
                    dest='reset',
                    action='store_true',
                    default=False,
                    help='Assign a new temporary password to a user.'),
        make_option('--setactive',
                    '-s',
                    dest='setactive',
                    action='store_true',
                    default=False,
                    help='Set a user account to active.'),
        make_option('--enabletotp',
                    '-t',
                    dest='enabletotp',
                    action='store_true',
                    default=False,
                    help='Enable TOTP for a user.'),
        make_option('--disabletotp',
                    '-T',
                    dest='disabletotp',
                    action='store_true',
                    default=False,
                    help='Disable TOTP for a user.'),
        make_option('--username',
                    '-u',
                    dest='username',
                    default=None,
                    help='Username for new user.'),
    )
    help = 'Add and edit a CRITs user. If "-a" is not used, we will try to edit.'

    def handle(self, *args, **options):
        """
        Script execution.
        """

        adduser = options.get('adduser')
        admin = options.get('admin')
        clearsecret = options.get('clearsecret')
        deactivate = options.get('deactivate')
        disabletotp = options.get('disabletotp')
        email = options.get('email')
        enabletotp = options.get('enabletotp')
        firstname = options.get('firstname')
        invalidreset = options.get('invalidreset')
        lastname = options.get('lastname')
        sendemail = options.get('sendemail')
        organization = options.get('organization')
        password = options.get('password')
        reset = options.get('reset')
        setactive = options.get('setactive')
        username = options.get('username')

        # We always need a username
        if not username:
            raise CommandError("Must provide a username.")
        user = CRITsUser.objects(username=username).first()

        # Generate a password if one is not provided
        if not password:
            password = self.temp_password()

        # If we've found a user with that username and we aren't trying to add a
        # new user...
        if user and not adduser:
            if admin:
                user.role = "Administrator"
            if clearsecret:
                user.secret = ""
            if deactivate and not setactive:
                user.is_active = False
            if disabletotp and not enabletotp:
                user.totp = False
            if email:
                user.email = email
            if enabletotp and not disabletotp:
                user.totp = True
            if firstname:
                user.first_name = firstname
            if lastname:
                user.last_name = lastname
            if invalidreset:
                user.invalid_login_attempts = 0
            if organization:
                user.organization = organization
            if reset:
                user.set_password(password)
            if setactive and not deactivate:
                user.is_active = True
            try:
                user.save()
                if reset:
                    print "New temporary password for %s: %s" % (username,
                                                                 password)
                print "User %s has been updated!" % username
            except Exception, e:
                raise CommandError("Error saving changes: %s" % str(e))
            if adduser:
                raise CommandError("User '%s' exists in CRITs!" % username)
        elif adduser:
            if not email:
                raise CommandError("Must provide an email address!")
            user = CRITsUser.create_user(username, password, email)
            user.first_name = firstname
            user.last_name = lastname
            user.is_staff = True
            user.save()
            user.organization = organization
            if admin:
                user.role = "Administrator"
            user.save()

            if sendemail:
                crits_config = CRITsConfig.objects().first()
                if crits_config.crits_email_end_tag:
                    subject = "New CRITs User Account" + crits_config.crits_email_subject_tag
                else:
                    subject = crits_config.crits_email_subject_tag + "New CRITs User Account"
                body = """You are receiving this email because someone has created a
CRITs account for you. If you feel like you have received this in
error, please ignore this email. Your account information is below:\n\n
"""
                body += "Username:\t%s\n" % username
                body += "Password:\t%s\n\n\n" % password
                body += """You should log in immediately and reset your password.\n
Thank you!
"""
                user.email_user(subject, body)

            self.stdout.write("User '%s' created successfully!" % username)
            self.stdout.write("\nTemp password: \t%s" % password)
            self.stdout.write("\n")
        else:
            raise CommandError("Cannot edit a user before they exist!")

    def temp_password(self):
        """
        Temporary password must match the password complexity regex.
        If we don't have one in the DB use the one out of settings.
        """

        crits_config = CRITsConfig.objects().first()
        if crits_config:
            pw_regex = crits_config.password_complexity_regex
        else:
            pw_regex = settings.PASSWORD_COMPLEXITY_REGEX
        rex = re.compile(pw_regex)
        chars = string.letters + string.digits + string.punctuation
        for i in xrange(20):
            passwd = ''
            while len(passwd) < 50:
                passwd += choice(chars)
                if rex.match(passwd):
                    return passwd
        raise CommandError("Unable to generate complex enough password.")
