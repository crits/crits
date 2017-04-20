import datetime
import threading

from django.utils.html import escape as html_escape

from mongoengine import EmbeddedDocument
try:
    from mongoengine.base import ValidationError
except ImportError:
    from mongoengine.errors import ValidationError
from mongoengine.base.datastructures import BaseList
from mongoengine.queryset import Q

from crits.core.class_mapper import class_from_id
from crits.core.form_consts import NotificationType
from crits.core.user import CRITsUser
from crits.core.user_tools import user_sources, get_subscribed_users
from crits.notifications.notification import Notification
from crits.notifications.processor import ChangeParser, MappedMongoFields
from crits.notifications.processor import NotificationHeaderManager


def create_notification(obj, username, message, source_filter=None,
                        notification_type=NotificationType.ALERT):
    """
    Generate a notification -- based on mongo obj.

    :param obj: The object.
    :type obj: class which inherits from
               :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param username: The user creating the notification.
    :type username: str
    :param message: The notification message.
    :type message: str
    :param source_filter: Filter on who can see this notification.
    :type source_filter: list(str)
    :param notification_type: The notification type (e.g. alert, error).
    :type notification_type: str
    """

    n = Notification()
    n.analyst = username
    obj_type = obj._meta['crits_type']
    users = set()

    if notification_type not in NotificationType.ALL:
        notification_type = NotificationType.ALERT

    n.notification_type = notification_type

    if obj_type == 'Comment':
        n.obj_id = obj.obj_id
        n.obj_type = obj.obj_type
        n.notification = "%s added a comment: %s" % (username, obj.comment)
        users.update(obj.users) # notify mentioned users

        # for comments, use the sources from the object that it is linked to
        # instead of the comments's sources
        obj = class_from_id(n.obj_type, n.obj_id)
    else:
        n.notification = message
        n.obj_id = obj.id
        n.obj_type = obj_type

    if hasattr(obj, 'source'):
        sources = [s.name for s in obj.source]
        subscribed_users = get_subscribed_users(n.obj_type, n.obj_id, sources)

        # Filter on users that have access to the source of the object
        for subscribed_user in subscribed_users:
            allowed_sources = user_sources(subscribed_user)

            for allowed_source in allowed_sources:
                if allowed_source in sources:
                    if source_filter is None or allowed_source in source_filter:
                        users.add(subscribed_user)
                        break
    else:
        users.update(get_subscribed_users(n.obj_type, n.obj_id, []))

    users.discard(username) # don't notify the user creating this notification
    n.users = list(users)
    if not len(n.users):
        return
    try:
        n.save()
    except ValidationError:
        pass

    # Signal potentially waiting threads that notification information is available
    for user in n.users:
        notification_lock = NotificationLockManager.get_notification_lock(user)
        notification_lock.acquire()

        try:
            notification_lock.notifyAll()
        finally:
            notification_lock.release()

def create_general_notification(username, target_users, header, link_url, message,
                                notification_type=NotificationType.ALERT):
    """
    Generate a general notification -- not based on mongo obj.

    :param obj: The object.
    :type obj: class which inherits from
               :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param username: The user creating the notification.
    :type username: str
    :param target_users: The list of users who will get the notification.
    :type target_users: list(str)
    :param header: The notification header message.
    :type header: list(str)
    :param link_url: A link URL for the header, specify None if there is no link.
    :type link_url: str
    :param message: The notification message.
    :type message: str
    :param notification_type: The notification type (e.g. alert, error).
    :type notification_type: str
    """

    if notification_type not in NotificationType.ALL:
        notification_type = NotificationType.ALERT

    n = Notification()
    n.analyst = username
    n.notification_type = notification_type
    n.notification = message
    n.header = header
    n.link_url = link_url

    for target_user in target_users:
        # Check to make sure the user actually exists
        user = CRITsUser.objects(username=target_user).first()
        if user is not None:
            n.users.append(target_user)

    # don't notify the user creating this notification
    n.users = [u for u in n.users if u != username]
    if not len(n.users):
        return
    try:
        n.save()
    except ValidationError:
        pass

    # Signal potentially waiting threads that notification information is available
    for user in n.users:
        notification_lock = NotificationLockManager.get_notification_lock(user)
        notification_lock.acquire()

        try:
            notification_lock.notifyAll()
        finally:
            notification_lock.release()

def generate_audit_notification(username, operation_type, obj, changed_fields,
                                what_changed, is_new_doc=False):
    """
    Generate an audit notification on the specific change, if applicable.
    This is called during an audit of the object, before the actual save
    to the database occurs.

    :param username: The user creating the notification.
    :type username: str
    :param operation_type: The type of operation (i.e. save or delete).
    :type operation_type: str
    :param obj: The object.
    :type obj: class which inherits from
               :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param changed_fields: A list of field names that were changed.
    :type changed_fields: list of str
    :param message: A message summarizing what changed.
    :type message: str
    :param is_new_doc: Indicates if the input obj is newly created.
    :type is_new_doc: bool
    """

    obj_type = obj._meta['crits_type']

    supported_notification = __supported_notification_types__.get(obj_type)

    # Check if the obj is supported for notifications
    if supported_notification is None:
        return

    if operation_type == "save":
        message = "%s updated the following attributes: %s" % (username,
                                                               what_changed)
    elif operation_type == "delete":
        header_description = generate_notification_header(obj)
        message = "%s deleted the following: %s" % (username,
                                                    header_description)

    if is_new_doc:
        sources = []

        if hasattr(obj, 'source'):
            sources = [s.name for s in obj.source]

        message = None
        target_users = get_subscribed_users(obj_type, obj.id, sources)
        header = generate_notification_header(obj)
        link_url = None

        if hasattr(obj, 'get_details_url'):
            link_url = obj.get_details_url()

        if header is not None:
            header = "New " + header

        create_general_notification(username,
                                    target_users,
                                    header,
                                    link_url,
                                    message)

    process_result = process_changed_fields(message, changed_fields, obj)

    message = process_result.get('message')
    source_filter = process_result.get('source_filter')

    if message is not None:
        message = html_escape(message)
        create_notification(obj, username, message, source_filter, NotificationType.ALERT)

def combine_source_filters(current_source_filters, new_source_filters):
    """
    Combines sources together in a restrictive way, e.g. combines sources
    like a boolean AND operation, e.g. the source must exist in both lists.
    The only exception is if current_source_filters == None, in which case the
    new_source_filters will act as the new baseline.

    :type current_source_filters: list of source names
    :param current_source_filters: list(str).
    :type new_source_filters: list of source names
    :param new_source_filters: list(str).
    :returns: str: Returns a list of combined source names.
    """

    combined_source_filters = []

    if current_source_filters is None:
        return new_source_filters
    else:
        for new_source_filter in new_source_filters:
            if new_source_filter in current_source_filters:
                combined_source_filters.append(new_source_filter)

    return combined_source_filters

def process_changed_fields(initial_message, changed_fields, obj):
    """
    Processes the changed fields to determine what actually changed.

    :param message: An initial message to include.
    :type message: str
    :param changed_fields: A list of field names that were changed.
    :type changed_fields: list of str
    :param obj: The object.
    :type obj: class which inherits from
               :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :returns: str: Returns a message indicating what was changed.
    """

    obj_type = obj._meta['crits_type']
    message = initial_message

    if message is None:
        message = ''

    source_filter = None

    for changed_field in changed_fields:

        # Fields may be fully qualified, e.g. source.1.instances.0.reference
        # So, split on the '.' character and get the root of the changed field
        base_changed_field = MappedMongoFields.get_mapped_mongo_field(obj_type, changed_field.split('.')[0])

        new_value = getattr(obj, base_changed_field, '')
        old_obj = class_from_id(obj_type, obj.id)
        old_value = getattr(old_obj, base_changed_field, '')

        change_handler = ChangeParser.get_changed_field_handler(obj_type, base_changed_field)

        if change_handler is not None:
            change_message = change_handler(old_value, new_value, base_changed_field)

            if isinstance(change_message, dict):
                if change_message.get('source_filter') is not None:
                    new_source_filter = change_message.get('source_filter')
                    source_filter = combine_source_filters(source_filter, new_source_filter)

                change_message = change_message.get('message')

            if change_message is not None:
                message += "\n" + change_message[:1].capitalize() + change_message[1:]
        else:
            change_field_handler = ChangeParser.generic_single_field_change_handler

            if isinstance(old_value, BaseList):

                list_value = None

                if len(old_value) > 0:
                    list_value = old_value[0]
                elif len(new_value) > 0:
                    list_value = new_value[0]

                if isinstance(list_value, basestring):
                    change_field_handler = ChangeParser.generic_list_change_handler
                elif isinstance(list_value, EmbeddedDocument):
                    change_field_handler = ChangeParser.generic_list_json_change_handler

            change_message = change_field_handler(old_value, new_value, base_changed_field)

            if isinstance(change_message, dict):
                if change_message.get('source_filter') is not None:
                    new_source_filter = change_message.get('source_filter')
                    combine_source_filters(source_filter, new_source_filter)

                change_message = change_message.get('message')

            if change_message is not None:
                message += "\n" + change_message[:1].capitalize() + change_message[1:]

    return {'message': message, 'source_filter': source_filter}

def get_notification_details(request, newer_than):
    """
    Generate the data to render the notification dialogs.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :param newer_than: A filter that specifies that only notifications
                       newer than this time should be returned.
    :type newer_than: str in ISODate format.
    :returns: arguments (dict)
    """

    username = request.user.username
    notifications_list = []
    notifications = None
    latest_notification_time = None
    lock = NotificationLockManager.get_notification_lock(username)
    timeout = 0

    # Critical section, check if there are notifications to be consumed.
    lock.acquire()
    try:
        notifications = get_user_notifications(username, newer_than=newer_than)

        if len(notifications) > 0:
            latest_notification_time = str(notifications[0].created)
        else:
            # no new notifications -- block until time expiration or lock release
            lock.wait(60)

            # lock was released, check if there is any new information yet
            notifications = get_user_notifications(username, newer_than=newer_than)

            if len(notifications) > 0:
                latest_notification_time = str(notifications[0].created)
    finally:
        lock.release()

    if latest_notification_time is not None:
        acknowledgement_type = request.user.get_preference('toast_notifications', 'acknowledgement_type', 'sticky')

        if acknowledgement_type == 'timeout':
            timeout = request.user.get_preference('toast_notifications', 'timeout', 30) * 1000

    for notification in notifications:
        obj = class_from_id(notification.obj_type, notification.obj_id)

        if obj is not None:
            link_url = obj.get_details_url()
            header = generate_notification_header(obj)
        else:
            if notification.header is not None:
                header = notification.header
            else:
                header = "%s %s" % (notification.obj_type, notification.obj_id)

            if notification.link_url is not None:
                link_url = notification.link_url
            else:
                link_url = None

        notification_type = notification.notification_type

        if notification_type is None or notification_type not in NotificationType.ALL:
            notification_type = NotificationType.ALERT

        notification_data = {
            "header": header,
            "message": notification.notification,
            "date_modified": str(notification.created.strftime("%Y/%m/%d %H:%M:%S")),
            "link": link_url,
            "modified_by": notification.analyst,
            "id": str(notification.id),
            "type": notification_type,
        }

        notifications_list.append(notification_data)

    return {
        'notifications': notifications_list,
        'newest_notification': latest_notification_time,
        'server_time': str(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")),
        'timeout': timeout,
    }

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

def remove_user_from_notification_id(username, id):
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

    Notification.objects(id=id).update(pull__users=username)
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

__supported_notification_types__ = {
    'Actor': 'name',
    'Campaign': 'name',
    'Certificate': 'md5',
    'Comment': 'object_id',
    'Domain': 'domain',
    'Email': 'id',
    'Event': 'id',
    'Indicator': 'id',
    'IP': 'ip',
    'PCAP': 'md5',
    'RawData': 'title',
    'Sample': 'md5',
    'Target': 'email_address',
}

class NotificationLockManager(object):
    """
    Manager class to handle locks for notifications.
    """

    __notification_mutex__ = threading.Lock()
    __notification_locks__ = {}

    @classmethod
    def get_notification_lock(cls, username):
        """
        @threadsafe

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


def generate_notification_header(obj):
    """
    Generates notification header information based upon the object -- this is
    used to preface the notification's context.

    Could possibly be used for "Favorites" descriptions as well.

    :param obj: The top-level object instantiated class.
    :type obj: class which inherits from
               :class:`crits.core.crits_mongoengine.CritsBaseAttributes`.
    :returns: str with a human readable identification of the object
    """

    generate_notification_header_handler = NotificationHeaderManager.get_header_handler(obj._meta['crits_type'])

    if generate_notification_header_handler is not None:
        return generate_notification_header_handler(obj)
    else:
        return "%s: %s" % (obj._meta['crits_type'], str(obj.id))
