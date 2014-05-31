echo 0 > /proc/sys/vm/zone_reclaim_mode
numactl --interleave=all mongod --configsvr --fork --logpath /var/log/mongodb_config.log --logappend --dbpath /data/configdb
