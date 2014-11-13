from django.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):
    """
    Script Class.
    """
    help = 'Creates the default dashboard.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """
        migrate_all_searches()
        
def migrate_all_searches():
    from crits.dashboards.models import SavedSearch
    multiplier = 2
    for search in SavedSearch.objects():
        if "left" in search and search.left > 0:
            search.col = search.left/2
        if "width" in search:
            search.sizex = search.width/2
        search.save()
        search.update(unset__left=1, unset__top=1, unset__width=1)
