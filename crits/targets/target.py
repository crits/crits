from mongoengine import Document, StringField, IntField, EmailField
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes
from crits.core.crits_mongoengine import CritsActionsDocument
from crits.core.user_tools import user_sources
from crits.emails.email import Email
from crits.targets.migrate import migrate_target

class Target(CritsBaseAttributes, CritsActionsDocument, Document):
    """
    Target class.
    """

    meta = {
        "collection": settings.COL_TARGETS,
        "crits_type": 'Target',
        "latest_schema_version": 3,
        "schema_doc": {
            'department': 'Target department name',
            'division': 'Target division',
            'email_address': 'Target email address',
            'email_count': 'Emails destined for this user. Added by MapReduce',
            'organization_id': 'Target organization ID number',
            'firstname': 'Target first name',
            'lastname': 'Target last name',
            'title': 'Target job title',
            'note': 'Custom note about target'
        },
        "jtable_opts": {
                         'details_url': 'crits.targets.views.target_info',
                         'details_url_key': 'email_address',
                         'default_sort': "email_count DESC",
                         'searchurl': 'crits.targets.views.targets_listing',
                         'fields': [ "email_address","firstname", "lastname",
                                     "email_count", "department", "division",
                                     "status", "id"],
                         'jtopts_fields': [ "details",
                                            "email_address",
                                            "firstname",
                                            "lastname",
                                            "email_count",
                                            "department",
                                            "division",
                                            "status",
                                            "favorite",
                                            "id"],
                         'hidden_fields': [],
                         'linked_fields': [ "department", "division" ],
                         'details_link': 'details',
                         'no_sort': ['details']
                       }

    }

    email_address = EmailField(required=True)
    email_count = IntField(default=0)
    department = StringField()
    division = StringField()
    organization_id = StringField()
    firstname = StringField()
    lastname = StringField()
    title = StringField()
    note = StringField()

    def migrate(self):
        migrate_target(self)

    def find_emails(self, username):
        sources = user_sources(username)
        emails = Email.objects(to__iexact=self.email_address,
                               source__name__in=sources)
        return emails
