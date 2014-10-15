import json

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse

from crits.core.class_mapper import class_from_id, details_url_from_obj
from crits.core.user_tools import user_can_view_data
from crits.notifications.handlers import get_user_notifications, remove_user_from_notification_id
from crits.notifications.handlers import NotificationLockManager


@user_passes_test(user_can_view_data)
def poll(request):
    """

    """

    # TODO Refactor from .views into .handlers

    newer_than = request.POST.get("newer_than", None)

    if newer_than == "":
        newer_than = None

    notifications_list = []
    notifications = None
    latest_notification = None
    lock = NotificationLockManager.get_notification_lock(request.user.username)

    # Critical section, check if there are notifications to be consumed.
    lock.acquire()
    try:
        notifications = get_user_notifications(request.user.username, newer_than=newer_than)

        if len(notifications) > 0:
            latest_notification = str(notifications[0].created)
        else:
            lock.wait(60)

            # lock was released, check if there is any new information yet
            notifications = get_user_notifications(request.user.username, newer_than=newer_than)

            if len(notifications) > 0:
                latest_notification = str(notifications[0].created)
    finally:
        lock.release()

    for notification in notifications:
        obj = class_from_id(notification.obj_type, notification.obj_id)
        details_url = details_url_from_obj(obj)

        # TODO Pass back the current server time back to the client
        # so that they know how to calculate the difference in time?
        # Alternatively we could have the server calculate it but that's
        # resources consumed on the server side.
        header = generate_notification_header(obj, "just now")

        notification_data = {
            "header": header,
            "message": notification.notification,
            "time_ago": "just now",
            "link": details_url,
            "id": str(notification.id),
        }

        notifications_list.append(notification_data)

    return HttpResponse(json.dumps({'notifications': notifications_list,
                                    'newest_notification': latest_notification}),
                        mimetype="application/json")

@user_passes_test(user_can_view_data)
def acknowledge(request):
    """
    Called to indicate a user acknowledgment of a specific notification.
    Users that acknowledge notifications will remove the user from
    that notification listing.
    """

    id = request.POST.get("id", None)

    remove_user_from_notification_id(request.user.username, id)

    return HttpResponse(json.dumps({}),
                        mimetype="application/json")

def generate_notification_header(obj, time_ago):
    """
    Generates notification header information based upon the object -- this is
    used to preface the notification's context.
    """

    type = obj._meta['crits_type']

    if type == "Domain":
        return "Domain: %s" % (obj.domain)
    else:
        return "%s: %s" % (type, str(obj.id))
