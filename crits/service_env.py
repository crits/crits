"""The first time this module is imported, all of the services are loaded and
configured. Importing this module from a second location will not cause them
to be reloaded."""

from django.conf import settings

from crits.services.core import AnalysisEnvironment
from crits.services.db import (DatabaseAnalysisSource,
    DatabaseAnalysisDestination, DatabaseServiceManager)

manager = DatabaseServiceManager(settings.SERVICE_DIRS)
source = DatabaseAnalysisSource()
dest = DatabaseAnalysisDestination()
environment = AnalysisEnvironment(manager, source, dest)
