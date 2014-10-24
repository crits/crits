from django.core.management.base import BaseCommand

from crits.core.role import Role

class Command(BaseCommand):
    """
    Script Class.
    """

    help = 'Creates the default UberAdmin Role in MongoDB.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        add_uber_admin_role(True)

def add_uber_admin_role(drop=False):
    """
    Add UberAdmin role to the system. This will always reset the UberAdmin role
    back to the original state if found in the database. If drop is set to True,
    all Roles will be removed and the default UberAdmin role will be added.

    The 'UberAdmin' role gets full access to *ALL* sources at the time it is
    created.

    :param drop: Drop collection before adding.
    :type drop: boolean
    """

    if drop:
        print "Drop protection disabled. Dropping all Roles!"
        Role.drop_collection()
    else:
        print ("Drop protection enabled!\n",
                "Resetting 'UberAdmin' Role to defaults!")
    role = Role.objects(name="UberAdmin").first()
    if not role:
        print "Could not find UberAdmin Role. Creating it!"
        role = Role()
        role.name = "UberAdmin"
        role.description = "Default role with full system access."
    role.add_all_sources()
    role.make_all_true()
    role.save()
