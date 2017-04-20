import sys
from optparse import OptionParser
import pymongo

parser = OptionParser()
parser.add_option("-o", "--opid", dest="opid", default=None,
                        help="specific operation to kill.")

(options, args) = parser.parse_args()

opids = []

if options.opid is not None:
    ops = options.opid.split(',')
    for op in ops:
        opids.append(op.strip())
else:
    data = sys.stdin.readlines()
    for d in data:
        opids.append(d.strip())

print "Kill Sequence:"
conn = pymongo.MongoClient()
# db.$cmd.sys.killop.findOne({op:1234})
for op in opids:
    print "Killing: %s" % op
    result = conn['admin']['$cmd.sys.killop'].find_one({'op': "%s" % op})
    print "\t%s" % result
