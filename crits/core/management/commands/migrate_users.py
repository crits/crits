import getpass
import MySQLdb as mdb

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option


"""
Migrates users from Django to MongoDB. We cannot use the Django model here
because settings.py will have no knowledge of how to connect to MySQL
after the code changes as well as the auth model in settings.py is set to our
custom one for MongoDB. Instead we are connecting to the database directly
using script arguments.
"""

class Command(BaseCommand):
    """
    Script Class.
    """

    option_list = BaseCommand.option_list + (
        make_option("-H",
                    "--host",
                    dest="hostname",
                    default=None,
                    help='Hostname, if not localhost.'),
        make_option("-u",
                    "--username",
                    dest="username",
                    default=None,
                    help='username to connect as.'),
        make_option("-d",
                    "--database",
                    dest="database",
                    default=None,
                    help='database to connect to.'),
        make_option("-p",
                    "--password",
                    dest="password",
                    default=None,
                    help='password. if not provided you will be prompted.'),
    )
    help = 'Migrates CRITs users to MongoDB.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        from crits.core.user import CRITsUser

        hostname = options.get('hostname')
        username = options.get('username')
        database = options.get('database')
        password = options.get('password')

        if not hostname:
            hostname = 'localhost'
        if not username or not database:
            raise CommandError('You must provide a username and database name')
        if not password:
            # force password entry to be manual
            password = getpass.getpass()

        try:
            con = None
            con = mdb.connect(hostname, username, password, database);
            cur = con.cursor(mdb.cursors.DictCursor)
            cur.execute("SELECT * FROM auth_user")
            rows = cur.fetchall()
        except mdb.Error, e:
           raise CommandError("Error %d: %s" % (e.args[0],e.args[1]))
        finally:
            if con:
                con.close()

        for du in rows:
            user = CRITsUser.objects(username=du['username']).first()
            if not user:
                user = CRITsUser()
                user.username = du['username']
            user.password = du['password']
            user.date_joined = du['date_joined']
            user.email = du['email']
            user.first_name = du['first_name']
            user.last_name = du['last_name']
            user.is_active = True if du['is_active'] else False
            user.is_staff = True if du['is_staff'] else False
            user.is_superuser = True if du['is_superuser'] else False
            user.last_login = du['last_login']
            user.save()
