#!/bin/sh
# Very basic script showing how to fork mongod.
# This also sets up a custom log file, disables the web interface,
# and sets the directory where the DB should be written to.
mongod --fork --logpath /data/logs/mongodb.log --logappend --nohttpinterface --dbpath /data/db
