echo 0 > /proc/sys/vm/zone_reclaim_mode
mongod --configsvr --fork --logpath /var/log/mongodb_config.log --logappend --dbpath /data/configdb
