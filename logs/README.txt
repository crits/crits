In a fresh, unmodified copy of CRITs, logs will be placed in this directory.

In a production instance, administrators should generally modify
custom_settings.py and set the LOG_DIRECTORY setting. LOG_DIRECTORY should be
writable by the Apache web server process running CRITs, as well as by any user
running scripts or cron jobs related to CRITs.
