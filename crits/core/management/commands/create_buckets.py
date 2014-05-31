from django.core.management.base import BaseCommand

from crits.core.s3_tools import s3_create_bucket
import settings

class Command(BaseCommand):
    """
    Script Class.
    """

    help = 'Create S3 buckets.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        s3_create_bucket(settings.BUCKET_OBJECTS + settings.S3_SEPARATOR + settings.S3_ID)
        s3_create_bucket(settings.BUCKET_PCAPS + settings.S3_SEPARATOR + settings.S3_ID)
        s3_create_bucket(settings.BUCKET_SAMPLES + settings.S3_SEPARATOR + settings.S3_ID)
