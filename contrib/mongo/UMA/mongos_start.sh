echo 0 > /proc/sys/vm/zone_reclaim_mode
mongos --fork --logpath /var/log/mongodb_router.log --logappend --nohttpinterface --configdb server1.example.com:27019,server2.example.com:27019,server3.example.com:27019
