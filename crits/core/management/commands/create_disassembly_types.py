from django.core.management.base import BaseCommand

from crits.disassembly.disassembly import DisassemblyType 

class Command(BaseCommand):
    """
    Script Class.
    """

    help = 'Creates Disassembly types in MongoDB.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        add_disassembly_types(True)

def add_disassembly_types(drop=False):
    """
    Populate default set of disassembly types into the system.

    :param drop: Drop the existing collection before trying to populate.
    :type: boolean
    """

    # Define the disassembly types here.
    data_types = ['IDA', 'Hopper']
    if drop:
        DisassemblyType.drop_collection()
    if len(DisassemblyType.objects()) < 1:
        for data_type in data_types:
            dt = DisassemblyType()
            dt.name = data_type
            dt.save()
        print "Disassembly Types: added %s types!" % len(data_types)
    else:
        print "Disassembly Types: existing documents detected. skipping!"
