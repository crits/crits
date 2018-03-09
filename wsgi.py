#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crits.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
else:
    # This application object is used by the development server
    # as well as any WSGI server configured to use this file.
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
