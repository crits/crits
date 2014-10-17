import json

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse

from crits.core.user_tools import user_can_view_data
from crits.notifications.handlers import remove_user_from_notification_id, get_notification_details


@user_passes_test(user_can_view_data)
def poll(request):
    """

    """

    is_toast_enabled = request.user.get_preference('toast_notifications', 'enabled', True)

    if is_toast_enabled:
        newer_than = request.POST.get("newer_than", None)

        if newer_than == "":
            newer_than = None

        data = get_notification_details(request, newer_than)

        return HttpResponse(json.dumps(data),
                            mimetype="application/json")
    else:
        # toast notifications are not enabled for this user, return an error
        return HttpResponse(status=403)

@user_passes_test(user_can_view_data)
def acknowledge(request):
    """
    Called to indicate a user acknowledgement of a specific notification.
    Users that acknowledge notifications will remove the user from
    that notification listing.
    """

    id = request.POST.get("id", None)

    remove_user_from_notification_id(request.user.username, id)

    return HttpResponse(json.dumps({}),
                        mimetype="application/json")
