"""Management utilities.

    Example Usage:
    - fab vagrant create_admin_user
    - fab vagrant runserver
"""

from fabric.api import cd, prompt, run, task
from fabtools.vagrant import vagrant

APP_ROOT = "/vagrant"


@task
def create_admin_user(username=None, firstname=None, lastname=None,
                     email=None, org=None):
    """Set up an administrative user."""
    while not username:
        username = prompt("Username: ")
    while not firstname:
        firstname = prompt("First name: ")
    while not lastname:
        lastname = prompt("Last name: ")
    while not email:
        email = prompt("Email address: ")
    while not org:
        org = prompt("Organization name: ")

    print("Adding a default admin account")
    cmd = 'python manage.py users -a -A -e "{}" -f "{}" -l "{}" -o "{}" -u "{}"'
    with cd(APP_ROOT):
        run(cmd.format(email, firstname, lastname, org, username))
    print("Make note of the above password so you can authenticate!")


@task
def runserver():
    """Run CRITs using the built-in runserver."""
    with cd(APP_ROOT):
        run("python manage.py runserver 0.0.0.0:8080")
