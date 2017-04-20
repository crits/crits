from bson import ObjectId
try:
    from mongoengine.base import ValidationError
except ImportError:
    from mongoengine.errors import ValidationError

from crits.core.data_tools import generate_qrcode
from crits.core.totp import gen_user_secret

from django.conf import settings

def is_user_favorite(analyst, type_, id_):
    """
    Check if an ID is in a user's favorites.

    :param analyst: The username.
    :type analyst: str
    :param type_: The type of the object.
    :type type_: str
    :param id_: The ID of the object.
    :type id_: str
    :returns: boolean
    """

    if analyst:
        from crits.core.user import CRITsUser
        user = CRITsUser.objects(username=analyst).first()
        if not user:
            return False

        if type_ in user.favorites:
            if str(id_) in user.favorites[type_]:
                return True
    return False


def user_sources(username):
    """
    Get the sources for a user.

    :param username: The user to lookup.
    :type username: str
    :returns: list
    """

    if username:
        from crits.core.user import CRITsUser
        username = str(username)
        try:
            user = CRITsUser.objects(username=username).first()
            if user:
                return user.sources
            else:
                return []
        except Exception:
            return []
    else:
        return []

def sanitize_sources(username, items):
    """
    Get the sources for a user and limit the items to only those the user should
    have access to.

    :param username: The user to lookup.
    :type username: str
    :param items: A list of sources.
    :type items: list
    :returns: list
    """

    user_source_list = user_sources("%s" % username)
    final_items = []
    for item in items:
        final_source = [src for src in item['source'] if src['name'] in user_source_list]
        item['source'] = final_source
        final_items.append(item)
    return final_items

def get_user_organization(username):
    """
    Get the organization for a user.

    :param username: The user to lookup.
    :type username: str
    :returns: str
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    if user:
        return user.organization
    else:
        return settings.COMPANY_NAME

def is_admin(username):
    """
    Determine if the user is an admin.

    :param username: The user to lookup.
    :type username: str
    :returns: True, False
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    if user:
        if user.role == "Administrator":
            return True
    return False

def get_user_role(username):
    """
    Get the user role.

    :param username: The user to lookup.
    :type username: str
    :returns: str
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    return user.role

def user_can_view_data(user):
    """
    Determine if the user is active and authenticated.

    :param user: The user to lookup.
    :type user: str
    :returns: True, False
    """

    if user.is_active:
        return user.is_authenticated()
    else:
        return False

def user_is_admin(user):
    """
    Determine if the user is an admin and authenticated and active.

    :param user: The user to lookup.
    :type user: str
    :returns: True, False
    """

    if user.is_active:
        if user.is_authenticated():
            return is_admin(user)
    return False

def get_user_list():
    """
    Get a list of users. Sort the list alphabetically and do not include
    subscriptions.

    :returns: list
    """

    from crits.core.user import CRITsUser
    users = CRITsUser.objects().order_by('+username').exclude('subscriptions')
    user_list = []
    user_list.append({'username': "", 'sources': [], 'role': ""})
    for user in users:
        user_list.append(user)
    return user_list

def get_user_info(username=None):
    """
    Get information for a specific user.

    :param username: The user to get info for.
    :type username: str
    :returns: :class:`crits.core.user.CRITsUser`
    """

    from crits.core.user import CRITsUser
    if username is not None:
        username = str(username)
        return CRITsUser.objects(username=username).first()
    else:
        return username

def add_new_user_role(name, analyst):
    """
    Add a new user role to the system.

    :param name: The name of the role.
    :type name: str
    :param analyst: The user adding the role.
    :type analyst: str
    :returns: True, False
    """

    from crits.core.user_role import UserRole
    name = name.strip()
    role = UserRole.objects(name=name).first()
    if not role:
        role = UserRole()
        role.name = name
        try:
            role.save(username=analyst)
            return True
        except ValidationError:
            return False
    else:
        return False

def get_user_email_notification(username):
    """
    Get user email notification preference.

    :param username: The user to query for.
    :type username: str
    :returns: str
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    return user.get_preference('notify', 'email', False)

def get_user_subscriptions(username):
    """
    Get user subscriptions.

    :param username: The user to query for.
    :type username: str
    :returns: list
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    return user.subscriptions

def get_subscribed_users(stype, oid, sources):
    """
    Get users subscribed to this top-level object.

    :param stype: The top-level object type.
    :type stype: str
    :param oid: The ObjectId of the top-level object.
    :type oid: str
    :returns: list
    :param sources: A list of sources of the top-level object.
    :type sources: list
    :returns: list
    """

    from crits.core.user import CRITsUser
    user_list = []
    query = { '$or': [
                       {'subscriptions.%s.id' % stype: ObjectId(oid)},
                       {'subscriptions.Source.name': { '$in': sources }}
                     ]
            }
    users = CRITsUser.objects(__raw__=query)
    for user in users:
        user_list.append(user.username)
    return user_list

def is_user_subscribed(username, stype, oid):
    """
    Determine if the user is subscribed to this top-level object.

    :param username: The user to query for.
    :type username: str
    :param stype: The top-level object type.
    :type stype: str
    :param oid: The ObjectId of the top-level object.
    :type oid: str
    :returns: boolean
    """

    from crits.core.user import CRITsUser
    username = str(username)
    query = {'username': username, 'subscriptions.%s.id' % stype: ObjectId(oid)}
    results = CRITsUser.objects(__raw__=query).first()
    if results is not None:
        return True
    else:
        return False

def is_user_subscribed_to_source(username, source):
    """
    Determine if the user is subscribed to this source.

    :param username: The user to query for.
    :type username: str
    :param source: The source name.
    :type source: str
    :returns: boolean
    """

    from crits.core.user import CRITsUser
    username = str(username)
    query = {'username': username, 'subscriptions.Source.name': source}
    results = CRITsUser.objects(__raw__=query).first()
    if results is not None:
        return True
    else:
        return False

def subscribe_user(username, stype, oid):
    """
    Subscribe a user to this top-level object.

    :param username: The user to query for.
    :type username: str
    :param stype: The top-level object type.
    :type stype: str
    :param oid: The ObjectId of the top-level object.
    :type oid: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    from crits.core.user import CRITsUser
    from crits.core.user import EmbeddedSubscription
    username = str(username)
    es = EmbeddedSubscription()
    es._id = oid
    user = CRITsUser.objects(username=username).first()
    if stype in user.subscriptions:
        user.subscriptions[stype].append(es)
    else:
        user.subscriptions[stype] = [es]
    try:
        user.save()
        return {'success': True}
    except ValidationError, e:
        return {'success': False,
                'message': e}

def unsubscribe_user(username, stype, oid):
    """
    Unsubscribe a user from this top-level object.

    :param username: The user to query for.
    :type username: str
    :param stype: The top-level object type.
    :type stype: str
    :param oid: The ObjectId of the top-level object.
    :type oid: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    for s in user.subscriptions[stype]:
        if str(s._id) == oid:
            user.subscriptions[stype].remove(s)
            break
    try:
        user.save()
        return {'success': True}
    except ValidationError, e:
        return {'success': False,
                'message': e}

def subscribe_to_source(username, source):
    """
    Subscribe a user to a source.

    :param username: The user to query for.
    :type username: str
    :param source: The name of the source.
    :type source: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    from crits.core.user import EmbeddedSourceSubscription
    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    es = EmbeddedSourceSubscription()
    es.name = source
    user.subscriptions['Source'].append(es)
    try:
        user.save()
        return {'success': True}
    except ValidationError, e:
        return {'success': False,
                'message': e}

def unsubscribe_from_source(username, source):
    """
    Unsubscribe a user from a source.

    :param username: The user to query for.
    :type username: str
    :param source: The name of the source.
    :type source: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    for s in user.subscriptions['Source']:
        if s.name == source:
            user.subscriptions['Source'].remove(s)
            break
    try:
        user.save()
        return {'success': True}
    except ValidationError, e:
        return {'success': False,
                'message': e}

def update_user_preference(username, section, values):
    """
    Update a user preference.

    :param username: The user to query for.
    :type username: str
    :param section: The section in their preferences.
    :type section: str
    :param values: The values to set.
    :type values: str, list, dict
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()

    if user:
        if not section in user.prefs:
           setattr(user.prefs, section, {})

        # Something to think about.. do we want to do a replacement or a merge?
        setattr(user.prefs, section, values)

        try:
            user.save()
            return {'success': True }
        except ValidationError, e:
            return {'success': False,
                    'message': e}
    return {'success': False,
            'message': "User not found"}

def get_nav_template(nav_preferences):
    """
    Returns the template for the navigation menu based on the nav preferences

    :param nav_preferences: The navigation preferences which is based
                            on :class:`crits.core.forms.NavMenuForm`
    :type nav_preferences: dict
    :returns: The navigation template for the specified navigation preference.
              If a navigation preference is not specified then None is returned.
    """
    if nav_preferences != None:
        nav_menu = nav_preferences.get("nav_menu")

        if nav_menu == "topmenu":
            return "topmenu.html"

    return None

def toggle_user_preference(username, section, setting, is_enabled=False):
    """
    Enables/Disables the target user preference

    :param username: The username that the preference toggle is for.
    :type username: str
    :param section: The section name where the preference is stored.
    :type section: str
    :param setting: The name of the setting within the section of the preference.
    :type setting: str
    :param is_enabled: An optional default value if the preference does not exist.
    :type is_enabled: str
    :returns: "success" (boolean), "message" (str) if failed,
              "state" (boolean) if successful
    """
    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()

    if user:
        # Split the preference option into subtrees on '.'
        otree = setting.split(".")
        param = otree.pop()

        if not section in user.prefs:
            setattr(user.prefs, section, {})
        opt = user.prefs[section]

        if len(otree):
            for subsect in otree:
                if not subsect in opt:
                    opt[subsect] = {}
                    opt = opt[subsect]
                else:
                    opt = opt[subsect]

        if (not param in opt):
            # if the preference doesn't exist, then try the fallback default value
            if is_enabled == True:
                opt[param] = False
            else:
                opt[param] = True
        else:
            # the preference exists, so use it
            if (not opt[param]):
                opt[param] = True
            else:
                opt[param] = False

        try:
            user.save()
            return {'success': True,
                    'state': opt[param] }
        except ValidationError, e:
            return {'success': False,
                    'message': e}
    return {'success': False,
            'message': "User not found"}

def get_email_address(username):
    """
    Get a user's email address.

    :param username: The user to query for.
    :type username: str
    :returns: str
    """

    from crits.core.user import CRITsUser
    username = str(username)
    return CRITsUser.objects.get(username=username).email

def change_user_password(username, current_p, new_p, new_p_c):
    """
    Change the password for a user.

    :param username: The user to query for.
    :type username: str
    :param current_p: The user's current password.
    :type current_p: str
    :param new_p: The new password.
    :type new_p: str
    :param new_p_c: New password confirmation.
    :type new_p_c: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    if new_p != new_p_c:
        return {'success': False, 'message': 'New password confirmation does not match.'}
    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    if not user:
        return {'success': False, 'message': 'Unknown user.'}
    if not user.check_password(current_p):
        return {'success': False, 'message': 'Current password invalid.'}
    if user.set_password(new_p, username):
        return {'success': True, 'message': 'Password Change Successful.'}
    else:
        from crits.config.config import CRITsConfig
        crits_config = CRITsConfig.objects().first()
        if crits_config:
            regex_desc = crits_config.password_complexity_desc
        else:
            regex_desc = settings.PASSWORD_COMPLEXITY_DESC
        return {'success': False,
                'message': 'Password not complex enough: %s' % regex_desc}

def toggle_active(username, analyst):
    """
    Toggle a user active/inactive.

    :param username: The user to query for.
    :type username: str
    :param analyst: The user toggling this user active/inactive.
    :type analyst: str
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    if user:
        if user.is_active:
            user.mark_inactive(analyst=analyst)
        else:
            user.mark_active(analyst=analyst)

def save_user_secret(username, totp_pass, title, size):
    """
    Save the TOTP secret for a user. If we can generate a QRCode for them to
    scan off the screen, we will return that as well.

    :param username: The user to save the secret for.
    :type username: str
    :param totp_pass: The secret to save.
    :type totp_pass: str
    :param title: The title for the QRCode.
    :type title: str
    :param size: The size of the QRCode image.
    :type size: tuple.
    :returns: dict with keys:
              "success" (boolean),
              "secret" (str),
              "qr_img" (str or None)
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    response = {}
    if user:
        (crypt_secret, totp_secret) = gen_user_secret(totp_pass, username)
        user.secret = crypt_secret
        user.totp = True
        user.save()
        response['success'] = True
        response['secret'] = totp_secret
        qr_img = generate_qrcode("otpauth://totp/%s?secret=%s" %
                                    (title, totp_secret), size)
        if qr_img:
            response['qr_img'] = qr_img
        else:
            response['qr_img'] = None
    else:
        response['success'] = False

    return response

def get_api_key_by_name(username, name):
    """
    Get a user's API key by the name.

    :param username: The user to search for.
    :type username: str
    :param name: The name of the API key.
    :type name: str
    :returns: str, None
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    if user:
        return user.get_api_key(name)
    return None

def create_api_key_by_name(username, name, default=False):
    """
    Create API key by the name.

    :param username: The user to search for.
    :type username: str
    :param name: The name of the API key.
    :type name: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    if user:
        return user.create_api_key(name, username, default=default)
    return {'success': False,
            'message': 'No user to create key for.'}

def make_default_api_key_by_name(username, name):
    """
    Make an API key the default by the name.

    :param username: The user to search for.
    :type username: str
    :param name: The name of the API key.
    :type name: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    if user:
        return user.default_api_key(name, username)
    return {'success': False,
            'message': 'No user to set default key for.'}

def revoke_api_key_by_name(username, name):
    """
    Revoke API key by the name.

    :param username: The user to search for.
    :type username: str
    :param name: The name of the API key.
    :type name: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    from crits.core.user import CRITsUser
    username = str(username)
    user = CRITsUser.objects(username=username).first()
    if user:
        return user.revoke_api_key(name, username)
    return {'success': False,
            'message': 'No user to revoke key for.'}
