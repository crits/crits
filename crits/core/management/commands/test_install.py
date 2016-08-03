import os
import platform
import subprocess
import sys

try:
    from django.core.management.base import BaseCommand, CommandError as CE
    from django.conf import settings
except ImportError:
    print "\tCould not import Django python module. Is it installed properly?"
    sys.exit(1)

class Command(BaseCommand):
    """
    Script Class.
    """

    help = 'Check the CRITs install for necessary modules and configurations.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        # Keep state in case we need to exit the test early
        fail = False

        # Test python imports
        imports = [ 'anyjson',
                   'bson',
                   'crits',
                   'dateutil',
                   'gridfs',
                   'importlib',
                   'lxml',
                   'M2Crypto',
                   'pyimpfuzzy',
                   'magic',
                   'mongoengine',
                   'nids',
                   'pymongo',
                   'pydeep',
                   'pyparsing',
                   'requests',
                   'yaml',
                   ]

        for i in imports:
            try:
                __import__(i)
            except ImportError:
                print CE('Could not import %s. Is it installed properly?' % i)
                # Required to continue script, so totally fail if these
                # are missing.
                if i in ('mongoengine', 'crits', 'pymongo'):
                    fail = True

        if fail:
            raise CE('Critical python modules missing. Cannot continue.')
            sys.exit(1)

        # Check for binaries
        binaries = ['7z',
                    'mongod',
                    'mongos',
                    'upx']

        cmd = "where" if platform.system() == "Windows" else "which"

        for i in binaries:
            try:
                op = subprocess.Popen([cmd, i], stdout=subprocess.PIPE)
                op.communicate()
                if op.returncode:
                    print CE('Could not find binary %s. Is it installed properly?' % i)
            except:
                print CE('Could not find binary %s. Is it installed properly?' % i)
                # Required to continue script, so totally fail if these
                # are missing.
                if i in ('mongod', 'mongos'):
                    fail = True

        if fail:
            raise CE('Critical binaries missing. Cannot continue.')
            sys.exit(1)

        # Check database is running and can connect to it
        try:
            import mongoengine
            if settings.MONGO_USER:
                mongoengine.connect(settings.MONGO_DATABASE,
                                    host=settings.MONGO_HOST,
                                    port=settings.MONGO_PORT,
                                    read_preference=settings.MONGO_READ_PREFERENCE,
                                    ssl=settings.MONGO_SSL,
                                    username=settings.MONGO_USER,
                                    password=settings.MONGO_PASSWORD)
            else:
                mongoengine.connect(settings.MONGO_DATABASE,
                                    host=settings.MONGO_HOST,
                                    port=settings.MONGO_PORT,
                                    read_preference=settings.MONGO_READ_PREFERENCE,
                                    ssl=settings.MONGO_SSL)
        except:
            raise CE('Could not connect to Mongo Database. Is it running'
                     ' and is CRITs configured to connect to it properly?')


        # Check Configurations
        import crits
        config = crits.config.config.CRITsConfig.objects().first()
        ld = config.log_directory
        if not os.path.exists(ld) and len(ld) > 0:
            print CE('Configured CRITs log directory does not exist: %s' % ld)
        td = config.temp_dir
        if not os.path.exists(td):
            print CE('Configured CRITs temp directory does not exist: %s' % td)
        zp = config.zip7_path
        if not os.path.exists(zp):
            print CE('Configured CRITs zip path does not exist: %s' % zp)
        for i in config.service_dirs:
            if not os.path.exists(i):
                print CE('Configured CRITs service directory does not exist: %s' % i)

        print ("Installation check completed. Please fix any above errors before"
               " attempting to use CRITs!")
