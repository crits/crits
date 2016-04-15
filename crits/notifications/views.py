import json

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.core.user_tools import user_can_view_data
from crits.notifications.handlers import remove_user_from_notification_id, get_notification_details


@user_passes_test(user_can_view_data)
def poll(request):
    """
    Called by clients to wait for notifications for the user. Clients will
    block for a period of time until either expiration or notification
    that a new notification is available.
    """

    is_user_toast_enabled = request.user.get_preference('toast_notifications', 'enabled', True)

    if is_user_toast_enabled and settings.ENABLE_TOASTS:
        if request.method == 'POST' and request.is_ajax():
            newer_than = request.POST.get("newer_than", None)

            if newer_than == "":
                newer_than = None

            data = get_notification_details(request, newer_than)

            # discount double check of enabled toasts, settings could
            # have changed since a long period of blocking.
            if is_user_toast_enabled and settings.ENABLE_TOASTS:
                return HttpResponse(json.dumps(data),
                                    content_type="application/json")
            else:
                return HttpResponse(status=403)
        else:
            error = "Expected AJAX POST"
            return render_to_response("error.html",
                                      {"error" : error },
                                      RequestContext(request))
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

    is_user_toast_enabled = request.user.get_preference('toast_notifications', 'enabled', True)

    if is_user_toast_enabled and settings.ENABLE_TOASTS:
        if request.method == 'POST' and request.is_ajax():
            id = request.POST.get("id", None)

            remove_user_from_notification_id(request.user.username, id)

            return HttpResponse(json.dumps({}),
                                content_type="application/json")
        else:
            error = "Expected AJAX POST"
            return render_to_response("error.html",
                                      {"error" : error },
                                      RequestContext(request))
    else:
        # toast notifications are not enabled for this user, return an error
        return HttpResponse(status=403)
