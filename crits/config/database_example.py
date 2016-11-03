# This is an example file. You should copy this to "database.py" and
# make your changes there.
# Modifying this example file will not change the settings that CRITs uses.


# MongoDB connection information
MONGO_HOST = 'localhost'      # server to connect to
MONGO_PORT = 27017            # port MongoD is running on
MONGO_DATABASE = 'crits'      # database name to connect to
# The following optional settings should only be changed if you specifically
# enabled and configured them during your MongoDB installation
# See http://docs.mongodb.org/v2.4/administration/security/ regarding implementation
MONGO_SSL = False             # whether MongoD has SSL enabled
MONGO_USER = ''               # mongo user with "readWrite" role in the database
MONGO_PASSWORD = ''           # password for the mongo user
MONGO_REPLICASET = None       # name of RS, if mongod in Replicaset

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

# If your S3 location is somewhere other than s3.amazonaws.com, then you
# can specify a different hostname here. (if needed)
#S3_HOSTNAME = ""
