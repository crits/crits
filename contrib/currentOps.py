from optparse import OptionParser
import pprint
import pymongo

def main():
    parser = OptionParser()
    parser.add_option("-s", "--seconds-running", dest="seconds", default=None,
                            help="search for current Ops where the secs_running is greater than or equal to this value")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                            help="verbose output on each operation found")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False,
                            help="quiet ouput. only prints operation ID values.")
    parser.add_option("-o", "--opid", dest="opid", default=None,
                            help="specific operation to get details on.")

    (options, args) = parser.parse_args()
    seconds = 0
    verbose = False
    quiet = False
    opid = None
    if options.seconds is not None:
        seconds = options.seconds
    if options.verbose:
        verbose = True
    if options.quiet:
        quiet = True
    if options.opid is not None:
        opid = options.opid
    conn = pymongo.MongoClient()
    all_ops = conn['admin']['$cmd.sys.inprog'].find_one('inprog')['inprog']
    sync_ops = []
    active_ops = []
    for op in all_ops:
        if op['op'] == "query":
            if op['query'].has_key('writebacklisten'):
                sync_ops.append(op)
            elif op.has_key('secs_running'):
                if op['ns'] != "local.oplog.rs":
                    if int(op['secs_running']) >= int(seconds):
                        if opid is not None:
                            if opid == op['opid']:
                                active_ops.append(op)
                        else:
                            active_ops.append(op)
    if verbose:
        print "SyncOps found: %d" % len(sync_ops)
        print "Operations found: %d" % len(active_ops)
    for op in active_ops:
        if options.verbose:
            pprint.pprint(op)
        elif quiet:
            print op['opid']
        else:
            print "ID: %s" % op['opid']
            print "\tSeconds Running: %s" % op['secs_running']

if __name__ == '__main__':
    main()
