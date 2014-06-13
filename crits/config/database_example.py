# This is an example file. You should copy this to "database.py" and
# make your changes there.
# Modifying this example file will not change the settings that CRITs uses.


# MongoDB connection information
MONGO_HOST = 'localhost'      # server to connect to
MONGO_PORT = 27017            # port MongoD is running on
MONGO_DATABASE = 'crits'      # database name to connect to
MONGO_SSL = False             # whether MongoD has SSL enabled
MONGO_USER = ''               # username used to authenticate to mongo (normally empty)
MONGO_PASSWORD = ''           # password for the mongo user

# Set this to a sufficiently long random string. We recommend running
# the following code from a python shell to generate the string and pasting
# the output here.
#
# from django.utils.crypto import get_random_string as grs
# print grs(50, 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')
SECRET_KEY = ''

# DB to use for files
FILE_DB = GRIDFS # Set to S3 (NO QUOTES) to use S3. You'll also want to set
                 # the stuff below and create your buckets.

# Separator to use in bucket names (if needed)
#S3_SEPARATOR = '.'

# Unique ID to append to bucket names (if needed)
#S3_ID=""

# S3 credentials (if needed)
#AWS_ACCESS_KEY_ID = ""
#AWS_SECRET_ACCESS_KEY = ""
