from django.core.management.base import BaseCommand

from crits.core.bucket import Bucket
from crits.core.class_mapper import class_from_type
from crits.core.mongo_tools import mongo_connector

class Command(BaseCommand):
    """
    Script Class.
    """

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        buckets = {}

        pipeline = [
            {'$match': {'$and': [{'bucket_list': {'$ne': []}},
                                 {'bucket_list': {'$exists': True}}]}}, # only TLOs with buckets
            {'$unwind': '$bucket_list'}, # split each bucket out of list
            {'$match': {'bucket_list': {'$ne': ''}}}, # ignore any empty string buckets
            {'$group': {'_id': {'tag': '$bucket_list', 'id': '$_id'}}}, # get unique per TLO
            {'$group': {'_id': '$_id.tag', 'count': {'$sum': 1}}}, # total bucket counts
        ]

        tlo_types = [
            'Actor', 'Campaign', 'Certificate', 'Domain', 'Email',
            'Event', 'Indicator', 'IP', 'PCAP', 'RawData', 'Signature',
            'Sample', 'Target',
        ]

        for tlo_type in tlo_types:
            coll = class_from_type(tlo_type)._meta['collection']
            result = mongo_connector(coll).aggregate(pipeline)
            for x in result['result']:
                bucket = x['_id']
                if bucket not in buckets:
                    buckets[bucket] = Bucket()
                    buckets[bucket].name = bucket
                setattr(buckets[bucket], tlo_type, x['count'])

        # Drop all existing buckets
        Bucket.objects().delete_one()

        for bucket in buckets.values():
            bucket.save()
