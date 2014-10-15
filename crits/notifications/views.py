import json

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse

from crits.core.user_tools import user_can_view_data
from crits.notifications.handlers import remove_user_from_notification_id, get_notification_details


@user_passes_test(user_can_view_data)
def poll(request):
    """

    """

    newer_than = request.POST.get("newer_than", None)

    if newer_than == "":
        newer_than = None

    data = get_notification_details(request.user.username, newer_than)

    return HttpResponse(json.dumps(data),
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
