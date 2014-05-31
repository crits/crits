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
        make_option('--username',
                    '-u',
                    dest='username',
                    default=None,
                    help='Username for new user.'),
        make_option('--firstname',
                    '-f',
                    dest='firstname',
                    default='',
                    help='First name of new user.'),
        make_option('--lastname',
                    '-l',
                    dest='lastname',
                    default='',
                    help='Last name of new user.'),
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
        make_option('--administrator',
                    '-a',
                    dest='admin',
                    action='store_true',
                    default=False,
                    help='Make this user an administrator.'),
        make_option('--organization',
                    '-o',
                    dest='organization',
                    default='',
                    help='Assign user to an organization/source.'),
    )
    help = 'Add a CRITs user.'

    def handle(self, *args, **options):
        """
        Script execution.
        """

        username = options.get('username')
        firstname = options.get('firstname')
        lastname = options.get('lastname')
        email = options.get('email')
        sendemail = options.get('sendemail')
        admin = options.get('admin')
        organization = options.get('organization')
        password = self.temp_password()

        if not username:
            raise CommandError("Must provide a username.")
        if not email:
            raise CommandError("Must provide an email address.")
        user = CRITsUser.objects(username=username).first()
        if user:
            raise CommandError("User '%s' exists in CRITs!" % username)
        else:
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
