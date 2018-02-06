from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from crits.config.config import CRITsConfig
from crits.notifications.notification import Notification

from crits.core.user import CRITsUser

class EmailNotification(object):

    body = ""
    email = None
    from_address = ""
    instance_url = ""
    subject = ""
    username = None

    def __init__(self, username=None, email=None):
        """
        Set the default subject, body, from address, and other bits.
        """

        # set the user and email address to send to
        self.username = username
        self.email = email

        # grab the CRITs url to use for links
        crits_config = CRITsConfig.objects().first()
        self.instance_url = crits_config.instance_url
        if self.instance_url.endswith("/"):
            self.instance_url = self.instance_url[:-1]

        # set the email address to send this email from
        self.from_address = crits_config.crits_email

        # setup the email subject
        if crits_config.crits_email_end_tag:
            self.subject = "CRITs: Subscriptions and Notifications" + crits_config.crits_email_subject_tag
        else:
            self.subject = crits_config.crits_email_subject_tag + "CRITs: Subscriptions and Notifications"

        # start the body of the email
        comments_url = self.instance_url + reverse('crits.comments.views.activity')
        self.body = "Here's info on the latest comments and updates to CRITs that you are subscribed to!\n\n"
        self.body += "For more info, check out the Activity page: %s\n\n" % comments_url

    def add_to_body(self, value):
        """
        Add more content to the email body.

        :param value: The content to add.
        :type value: str
        """

        self.body += value

    def set_subject(self, value):
        """
        Set the email subject.

        :param value: The value of the subject.
        :type value: str
        """

        self.subject = value

    def create_notification(self, notification):
        """
        Create an email entry for a notification.

        :param notification: The notification to deal with.
        :type notification: :class:`crits.notifications.notification.Notification`
        :returns: str
        """
        url = "%s/details/%s/%s/" % (self.instance_url,
                                     notification.obj_type,
                                     notification.obj_id)
        value = '\t%s updated a(n) %s you are subscribed to: %s\n' % \
                    (notification.analyst, notification.obj_type, url)
        return value

    def send_email(self):
        send_mail(self.subject,
                  self.body,
                  self.from_address,
                  [self.email])

class Command(BaseCommand):
    """
    generate_notifications Django command
    """

    help = "Sends notifications to users via email."

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        # only look for active users who want email notifications
        users = CRITsUser.objects(is_active=True,
                                  prefs__notify__email=True)
        # only get the unprocessed notifications
        notifications = Notification.objects(status='new')

        for user in users:
            # only include notifications where the user is in the users list and
            # it wasn't created by them.
            includes = [x for x in notifications if user.username in x.users and user.username != x.analyst and x.obj_id != None]

            # only send an email if there's something to send
            if len(includes):
                email = EmailNotification(username=user.username,
                                        email=user.email)
                for include in includes:
                    email.add_to_body(email.create_notification(include))
                email.send_email()

        # clean up after ourselves
        usernames = [u.username for u in users]
        self.process_notifications(notifications, usernames)

    # mark notifications and comments as processed so we don't re-notify people
    def process_notifications(self, notifications, users):
        """
        Set notifications to processed. Remove users from the list if they
        received an email. If any notification has 0 users left, remove it.
        Also remove any processed notifications with 0 users left.

        :param notifications: The list of notifications to work with.
        :type notifications: list
        :param users: The users to work with.
        :type users: list
        """

        old = Notification.objects(status='processed').only('users')
        for oldn in old:
            if not len(oldn.users):
                oldn.delete()

        for notice in notifications:
            notice.users = [u for u in notice.users if u not in users]
            if not len(notice.users):
                notice.delete()
            else:
                notice.set_status('processed')
                notice.save()
