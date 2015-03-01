#!/bin/sh
# Very basic script showing how to fork mongod.
# This also sets up a custom log file, disables the web interface,
# and sets the directory where the DB should be written to.
# NOTE: use of smallfiles is for smaller systems (like VMs) who cannot
# allocate enough space for normal journal files.
mongod --fork --logpath /data/logs/mongodb.log --logappend --nohttpinterface --dbpath /data/db --smallfiles
