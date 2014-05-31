# example override.py
#
# This file can be used to overide or extend the settings in settings.py
#
# This is an example file. You should copy this to "overrides.py" and
# make your changes there.
# Modifying this example file will not change the settings that CRITs uses.
#
# The preferred way to configure most settings is using the
# crits_config database (configurable in the admin section of the UI).
#
# However this file is still useful for settings that either are not
# in the database or you want to override other items that cannot be
# done in other ways such as adding django apps or settings.  Other
# examples below related to develement environment peculiarities.
# (The overides.py file is in the excludes list so git does not track it)
#
# Using this file is better than editing settings.py directly so you
# won't need to merge future updates of settings.py.


# Reverse Proxy Setups:
# 
# An example for a dev environment,
# Using apache as a reverse proxy, Apache is configured to do authentication (AuthzLDAP)
#
# Relative proxy pass config:

        # ProxyPass http://localhost:8001/ retry=0
        # ProxyPassReverse http://localhost:8001/

        # RewriteEngine On
        # RewriteCond %{LA-U:REMOTE_USER} (.+)
        # RewriteRule . - [E=RU:%1]
        # RequestHeader set Remote-User %{RU}e
        # RequestHeader set X-Forwarded-Protocol "https"

# Now given that we're getting a Remote-User header, configure crits to use that.
#
# WARNING: If you enable this, be 100% certain your backend is not
# directly accessible and this header could be spoofed by an attacker,
# as can be seen above, we are making our backend listen on localhost.

# REMOTE_USER_META = 'HTTP_REMOTE_USER'
