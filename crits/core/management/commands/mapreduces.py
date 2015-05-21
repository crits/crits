from django.core.management.base import BaseCommand
import crits.stats.handlers as stats

class Command(BaseCommand):
    """
    Script Class.
    """

    help = "Runs mapreduces for CRITs."

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        stats.generate_yara_hits()
        stats.generate_sources()
        stats.generate_filetypes()
        stats.generate_filetypes()
        stats.generate_campaign_stats()
        stats.generate_counts()
        stats.target_user_stats()
        stats.campaign_date_stats()
