from crits.notifications.notification import Notification
from mongoengine.queryset import Q

import threading

def get_notifications_for_id(username, obj_id, obj_type):
    """
    Get notifications for a specific top-level object and user.

    :param username: The user to search for.
    :param obj_id: The ObjectId to search for.
    :type obj_id: str
    :param obj_type: The top-level object type.
    :type obj_type: str
    :returns: :class:`crits.core.crits_mongoengine.CritsQuerySet`
    """

    return Notification.objects(users=username,
                                obj_id=obj_id,
                                obj_type=obj_type)

def remove_notification(obj_id):
    """
    Remove an existing notification.

    :param obj_id: The top-level ObjectId to find the notification to remove.
    :type obj_id: str
    :returns: dict with keys "success" (boolean) and "message" (str).
    """

    notification = Notification.objects(id=obj_id).first()
    if not notification:
        message = "Could not find notification to remove!"
        result = {'success': False, 'message': message}
    else:
        notification.delete()
        message = "Notification removed successfully!"
        result = {'success': True, 'message': message}
    return result

def get_new_notifications():
    """
    Get any new notifications.
    """

    return Notification.objects(status="new")

def remove_user_from_notification(username, obj_id, obj_type):
    """
    Remove a user from the list of users for a notification.

    :param username: The user to remove.
    :type username: str
    :param obj_id: The ObjectId of the top-level object for this notification.
    :type obj_id: str
    :param obj_type: The top-level object type.
    :type obj_type: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    Notification.objects(obj_id=obj_id,
                         obj_type=obj_type).update(pull__users=username)
    return {'success': True}

def remove_user_notifications(username):
    """
    Remove a user from all notifications.

    :param username: The user to remove.
    :type username: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    Notification.objects(users=username).update(pull__users=username)


def get_user_notifications(username, count=False, newer_than=None):
    """
    Get the notifications for a user.

    :param username: The user to get notifications for.
    :type username: str
    :param count: Only return the count.
    :type count:bool
    :returns: int, :class:`crits.core.crits_mongoengine.CritsQuerySet`
    """
    n = None

    if newer_than is None or newer_than == None:
        n = Notification.objects(users=username).order_by('-created')
    else:
        n = Notification.objects(Q(users=username) & Q(created__gt=newer_than)).order_by('-created')

    if count:
        return len(n)
    else:
        return n

class NotificationLockManager(object):
    """
    Manager class to handle locks for notifications.
    """
    __notification_mutex__ = threading.Lock()
    __notification_locks__ = {}

    @classmethod
    def get_notification_lock(cls, username):
        """
        @Threadsafe

        Gets a notification lock for the specified user, if it doesn't exist
        then one is created.
        """

        if username not in cls.__notification_locks__:
            # notification lock doesn't exist for user, create new lock
            cls.__notification_mutex__.acquire()
            try:
                # safe double checked locking
                if username not in cls.__notification_locks__:
                    cls.__notification_locks__[username] = threading.Condition()
            finally:
                cls.__notification_mutex__.release()

        return cls.__notification_locks__.get(username)
