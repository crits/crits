echo 0 > /proc/sys/vm/zone_reclaim_mode
mongod --fork --logpath /var/log/mongodb.log --logappend --nohttpinterface
