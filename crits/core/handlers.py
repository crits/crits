import cgi
import os
import datetime
import HTMLParser
import json
import logging
import re
import ushlex as shlex
import urllib

from bson.objectid import ObjectId
from django.conf import settings
from django.contrib.auth import authenticate, login as user_login
from django.core.urlresolvers import reverse, resolve, get_script_prefix
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.html import escape as html_escape
from django.utils.http import urlencode
from mongoengine.base import ValidationError
from operator import itemgetter

from crits.config.config import CRITsConfig
from crits.core.audit import AuditLog
from crits.core.bucket import Bucket
from crits.core.class_mapper import class_from_id, class_from_type, key_descriptor_from_obj_type
from crits.core.crits_mongoengine import Releasability, json_handler
from crits.core.crits_mongoengine import CritsSourceDocument
from crits.core.source_access import SourceAccess
from crits.core.data_tools import create_zip, format_file
from crits.core.mongo_tools import mongo_connector, get_file
from crits.core.sector import Sector, SectorObject
from crits.core.user import CRITsUser, EmbeddedSubscriptions
from crits.core.user import EmbeddedLoginAttempt
from crits.core.user_tools import user_sources, is_admin
from crits.core.user_tools import save_user_secret
from crits.core.user_tools import get_user_email_notification

from crits.actors.actor import Actor
from crits.backdoors.backdoor import Backdoor
from crits.campaigns.campaign import Campaign
from crits.certificates.certificate import Certificate
from crits.comments.comment import Comment
from crits.domains.domain import Domain
from crits.events.event import Event
from crits.exploits.exploit import Exploit
from crits.ips.ip import IP
from crits.notifications.handlers import get_user_notifications, generate_audit_notification
from crits.pcaps.pcap import PCAP
from crits.raw_data.raw_data import RawData
from crits.emails.email import Email
from crits.samples.sample import Sample
from crits.screenshots.screenshot import Screenshot
from crits.targets.target import Target
from crits.indicators.indicator import Indicator

from crits.core.totp import valid_totp


logger = logging.getLogger(__name__)

def description_update(type_, id_, description, analyst):
    """
    Change the description of a top-level object.

    :param type_: The CRITs type of the top-level object.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :param description: The description to use.
    :type description: str
    :param analyst: The user setting the description.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    klass = class_from_type(type_)
    if not klass:
        return {'success': False, 'message': 'Could not find object.'}

    if hasattr(klass, 'source'):
        sources = user_sources(analyst)
        obj = klass.objects(id=id_, source__name__in=sources).first()
    else:
        obj = klass.objects(id=id_).first()
    if not obj:
        return {'success': False, 'message': 'Could not find object.'}

    # Have to unescape the submitted data. Use unescape() to escape
    # &lt; and friends. Use urllib2.unquote() to escape %3C and friends.
    h = HTMLParser.HTMLParser()
    description = h.unescape(description)
    try:
        obj.description = description
        obj.save(username=analyst)
        return {'success': True, 'message': "Description set."}
    except ValidationError, e:
        return {'success': False, 'message': e}

def get_favorites(analyst):
    """
    Get all favorites for a user.

    :param analyst: The username.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "results" (string)
    """

    user = CRITsUser.objects(username=analyst).first()
    if not user:
        return {'success': False, 'message': '<div id="favorites_results">Could not find user.</div>'}

    favorites = user.favorites.to_dict()
    if not favorites:
        return {'success': True, 'message': '<div id="favorites_results">You have no favorites.</div>'}

    field_dict = {
        'Actor': 'name',
        'Backdoor': 'name',
        'Campaign': 'name',
        'Certificate': 'filename',
        'Comment': 'object_id',
        'Domain': 'domain',
        'Email': 'id',
        'Event': 'title',
        'Exploit': 'name',
        'Indicator': 'id',
        'IP': 'ip',
        'PCAP': 'filename',
        'RawData': 'title',
        'Sample': 'filename',
        'Screenshot': 'id',
        'Target': 'email_address'
    }

    results = '''
              <table>
                  <tbody>
              '''

    for type_, attr in field_dict.iteritems():
        if type_ in favorites:
            ids = [ObjectId(s) for s in favorites[type_]]
            objs = class_from_type(type_).objects(id__in=ids).only(attr)
            for obj in objs:
                obj_attr = getattr(obj, attr)
                results += '<tr><td>%s</td><td><a href="%s">%s</a></td>' % (type_,
                    reverse('crits.core.views.details',
                             args=(type_, str(obj.id))),
                    obj_attr)
                results += '<td><span class="ui-icon ui-icon-trash remove_favorite favorites_icon_active" '
                results += 'data-type="%s" data-id="%s"></span></td><td width="5px"></td></tr>' % (type_, str(obj.id))
    results += '</tbody></table>'

    return {'success': True, 'results': results}


def favorite_update(type_, id_, analyst):
    """
    Toggle the favorite of a top-level object in a user profile on or off.

    :param type_: The CRITs type of the top-level object.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :param analyst: The user toggling the favorite.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    user = CRITsUser.objects(username=analyst).first()
    if not user:
        return {'success': False, 'message': 'Could not find user.'}

    if id_ in user.favorites[type_]:
        user.favorites[type_].remove(id_)
    else:
        user.favorites[type_].append(id_)

    try:
        user.save()
    except:
        pass

    return {'success': True}


def status_update(type_, id_, value="In Progress", analyst=None):
    """
    Update the status of a top-level object.

    :param type_: The CRITs type of the top-level object.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :param value: The status to set it to.
    :type value: str
    :param analyst: The user setting the status.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    obj = class_from_id(type_, id_)
    if not obj:
        return {'success': False, 'message': 'Could not find object.'}
    try:
        obj.set_status(value)
        obj.save(username=analyst)
        return {'success': True, 'value': value}
    except ValidationError, e:
        return {'success': False, 'message': e}


def get_data_for_item(item_type, item_id):
    """
    Get a minimal amount of data for the passed item.
    Used by the clipboard to provide selected item information.

    :param item_type: Item type (Domain, Indicator, etc...)
    :type item_type: str
    :param item_id: Item database ID (_id)
    :type item_id: str
    :returns: dict -- Contains the item data
    """

    type_to_fields = {
        'Actor': ['name', ],
        'Backdoor': ['name', ],
        'Campaign': ['name', ],
        'Certificate': ['filename', ],
        'Domain': ['domain', ],
        'Email': ['from_address', 'date', ],
        'Event': ['title', 'event_type', ],
        'Exploit': ['name', 'cve', ],
        'Indicator': ['value', 'ind_type', ],
        'IP': ['ip', 'type', ],
        'PCAP': ['filename', ],
        'RawData': ['title', ],
        'Sample': ['filename', ],
        'Target': ['email_address', ],
    }
    response = {'OK': 0, 'Msg': ''}
    if not item_id or not item_type:
        response['Msg'] = "No item data provided"
        return response
    if not item_type in type_to_fields:
        response['Msg'] = "Invalid item type: %s" % item_type
        return response

    doc = class_from_id(item_type, item_id)
    if not doc:
        response['Msg'] = "Item not found"
        return response
    response['OK'] = 1
    response['data'] = {}
    for field in type_to_fields[item_type]:
        if field in doc:
            value = doc[field]
            if len(value) > 30:
                saved = value
                value = saved[:15]
                value += '...'
                value += saved[-15:]
            response['data'][field.title()] = value
    return response

def add_releasability(type_, id_, name, user, **kwargs):
    """
    Add releasability to a top-level object.

    :param type_: The CRITs type of the top-level object.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :param name: The source to add releasability for.
    :type name: str
    :param user: The user adding the releasability.
    :type user: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    obj = class_from_id(type_, id_)
    if not obj:
        return {'success': False,
                'message': "Could not find object."}
    try:
        obj.add_releasability(name=name, analyst=user, instances=[])
        obj.save(username=user)
        obj.reload()
        return {'success': True,
                'obj': obj.to_dict()['releasability']}
    except Exception, e:
        return {'success': False,
                'message': "Could not add releasability: %s" % e}

def add_releasability_instance(type_, _id, name, analyst):
    """
    Add releasability instance to a top-level object.

    :param type_: The CRITs type of the top-level object.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :param name: The source to add releasability instance for.
    :type name: str
    :param analyst: The user adding the releasability instance.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    obj = class_from_id(type_, _id)
    if not obj:
        return {'success': False,
                'message': "Could not find object."}
    try:
        date = datetime.datetime.now()
        ri = Releasability.ReleaseInstance(analyst=analyst, date=date)
        obj.add_releasability_instance(name=name, instance=ri)
        obj.save(username=analyst)
        obj.reload()
        return {'success': True,
                'obj': obj.to_dict()['releasability']}
    except Exception, e:
        return {'success': False,
                'message': "Could not add releasability instance: %s" % e}

def remove_releasability_instance(type_, _id, name, date, analyst):
    """
    Remove releasability instance from a top-level object.

    :param type_: The CRITs type of the top-level object.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :param name: The source to remove releasability instance from.
    :type name: str
    :param date: The date of the instance being removed.
    :type date: datetime.datetime
    :param analyst: The user removing the releasability instance.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    obj = class_from_id(type_, _id)
    if not obj:
        return {'success': False,
                'message': "Could not find object."}
    try:
        obj.remove_releasability_instance(name=name, date=date)
        obj.save(username=analyst)
        obj.reload()
        return {'success': True,
                'obj': obj.to_dict()['releasability']}
    except Exception, e:
        return {'success': False,
                'message': "Could not remove releasability instance: %s" % e}

def remove_releasability(type_, _id, name, analyst):
    """
    Remove releasability from a top-level object.

    :param type_: The CRITs type of the top-level object.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :param name: The source to remove from releasability.
    :type name: str
    :param analyst: The user removing the releasability.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    obj = class_from_id(type_, _id)
    if not obj:
        return {'success': False,
                'message': "Could not find object."}
    try:
        obj.remove_releasability(name=name)
        obj.save(username=analyst)
        obj.reload()
        return {'success': True,
                'obj': obj.to_dict()['releasability']}
    except Exception, e:
        return {'success': False,
                'message': "Could not remove releasability: %s" % e}

def sanitize_releasability(releasability, user_sources):
    """
    Remove any releasability that is for sources a user does not have access to
    see.

    :param releasability: The releasability list for a top-level object.
    :type releasability: list
    :param user_sources: The sources a user has access to.
    :type user_sources: list
    :returns: list
    """

    # currently this uses dictionary lookups.
    # when we move to classes, this should use attributes
    return [r for r in releasability if r['name'] in user_sources]

def ui_themes():
    """
    Return a list of available UI themes.

    :returns: list
    """

    ui_themes = os.listdir(os.path.join(settings.MEDIA_ROOT,
                                        'css/jquery-themes'))
    return ui_themes

def does_source_exist(source, active=False):
    """
    Determine if a source exists.

    :param source: The name of the source to search for.
    :type source: str
    :param active: Whether the source also needs to be marked as active or not.
    :type active: boolean
    :returns: True, False
    """

    query = {'name': source}
    if active:
        query['active'] = 'on'
    if len(SourceAccess.objects(__raw__=query)) > 0:
        return True
    else:
        return False

def add_new_source(source, analyst):
    """
    Add a new source to CRITs.

    :param source: The name of the new source.
    :type source: str
    :param analyst: The user adding the new source.
    :type analyst: str
    :returns: True, False
    """

    try:
        source = source.strip()
        src = SourceAccess.objects(name=source).first()
        if src:
            return False
        src = SourceAccess()
        src.name = source
        src.save(username=analyst)
        return True
    except ValidationError:
        return False

def merge_source_lists(left, right):
    """
    Merge source lists takes two source list objects and merges them together.
    Left can be an empty list and it will set the list to be the right list for
    you. We will always return the left list.

    :param left: Source list one.
    :type left: list
    :param right: Source list two.
    :type right: list
    :returns: list
    """

    if left is None:
        return right
    elif len(left) < 1:
        return right
    else:
        #if two sources have the same name and same date, we can assume they're
        #   the same instance
        left_name_dates = {}
        for i in left:
            left_name_dates[i['name']] = [inst['date'] for inst in i['instances']]
        for src in right:
            match = False
            for s in left:
                if src['name'] == s['name']:
                    match = True
                    left_dates = left_name_dates[s['name']]
                    for i in src['instances']:
                        if i['date'] not in left_dates:
                            s['instances'].append(i)
            if not match:
                left.append(src)
    return left

def source_add_update(obj_type, obj_id, action, source, method='',
                      reference='', date=None, analyst=None):
    """
    Add or update a source for a top-level object.

    :param obj_type: The CRITs type of the top-level object.
    :type obj_type: str
    :param obj_id: The ObjectId to search for.
    :type obj_id: str
    :param action: Whether or not we are doing an "add" or "update".
    :type action: str
    :param source: The name of the source.
    :type source: str
    :param method: The method of data acquisition for the source.
    :type method: str
    :param reference: The reference to the data for the source.
    :type reference: str
    :param date: The date of the instance to add/update.
    :type date: datetime.datetime
    :param analyst: The user performing the add/update.
    :type analyst: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
              "object" (if successful)
                :class:`crits.core.crits_mongoengine.EmbeddedSource.SourceInstance`
    """

    obj = class_from_id(obj_type, obj_id)
    if not obj:
        return {'success': False,
                'message': 'Unable to find object in database.'}
    try:
        if action == "add":
            obj.add_source(source=source,
                        method=method,
                        reference=reference,
                        date=date,
                        analyst=analyst)
        else:
            obj.edit_source(source=source,
                            method=method,
                            reference=reference,
                            date=date,
                            analyst=analyst)
        obj.save(username=analyst)
        obj.reload()
        obj.sanitize_sources(username=analyst)
        if not obj.source:
            return {'success': False,
                    'message': 'Object has no sources.'}
        for s in obj.source:
            if s.name == source:
                if action == "add":
                    return {'success': True,
                            'object': s,
                            'message': "Source addition successful!"}
                else:
                    for i in s.instances:
                        if i.date == date:
                            return {'success': True,
                                    'object': s,
                                    'instance': i,
                                    'message': "Source addition successful!"}
                break
        return {'success': False,
                'message': ('Could not make source changes. '
                            'Refresh page and try again.')}
    except ValidationError, e:
        return {'success':False, 'message': e}

def source_remove(obj_type, obj_id, name, date, analyst=None):
    """
    Remove a source instance from a top-level object.

    :param obj_type: The CRITs type of the top-level object.
    :type obj_type: str
    :param obj_id: The ObjectId to search for.
    :type obj_id: str
    :param name: The name of the source.
    :type name: str
    :param date: The date of the instance to remove.
    :type date: datetime.datetime
    :param analyst: The user performing the removal.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    obj = class_from_id(obj_type, obj_id)
    if not obj:
        return {'success': False,
                'message': 'Unable to find object in database.'}
    try:
        result = obj.remove_source(source=name,
                                   date=date)
        obj.save(username=analyst)
        return result
    except ValidationError, e:
        return {'success':False, 'message': e}

def source_remove_all(obj_type, obj_id, name, analyst=None):
    """
    Remove a source from a top-level object.

    :param obj_type: The CRITs type of the top-level object.
    :type obj_type: str
    :param obj_id: The ObjectId to search for.
    :type obj_id: str
    :param name: The name of the source.
    :type name: str
    :param analyst: The user performing the removal.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    obj = class_from_id(obj_type, obj_id)
    if not obj:
        return {'success': False,
                'message': 'Unable to find object in database.'}
    try:
        result = obj.remove_source(source=name,
                                   remove_all=True)
        obj.save(username=analyst)
        return result
    except ValidationError, e:
        return {'success':False, 'message': e}

def get_object_types(active=True, query=None):
    """
    Get a list of available ObjectTypes in CRITs sorted alphabetically.

    :param active: Whether or not the ObjectTypes returned should be active.
    :type active: boolean
    :param query: Custom query to use by default.
    :type query: dict
    :returns: list
    """

    from crits.objects.object_type import ObjectType
    if query is None:
        query = {}
    if active:
        query['active'] = "on"
    result = ObjectType.objects(__raw__=query)
    object_types = []
    for r in result:
        if r.name == r.object_type:
            object_types.append((r.name, r.datatype))
        else:
            object_types.append(("%s - %s" % (r.object_type, r.name),
                                 r.datatype))
    object_types.sort()
    return object_types

def get_sources(obj_type, obj_id, analyst):
    """
    Get a list of sources for a top-level object.

    :param obj_type: The CRITs type of the top-level object.
    :type obj_type: str
    :param obj_id: The ObjectId to search for.
    :type obj_id: str
    :param analyst: The user performing the search.
    :type analyst: str
    :returns: list if successful or dict with keys "success" (boolean) and
              "message" (str)
    """

    obj = class_from_id(obj_type, obj_id)
    if not obj:
        return {'success': False,
                'message': 'Unable to find object in database.'}
    obj.sanitize_sources(username=analyst)
    return obj.source

def get_source_names(active=False, limited=False, username=None):
    """
    Get a list of available sources in CRITs sorted alphabetically.

    :param active: Whether or not the sources returned should be active.
    :type active: boolean
    :param limited: If the sources should be limited to only those the user has
                    access to.
    :type limited: boolean
    :param username: The user requesting the source list.
    :type username: str
    :returns: list
    """

    query = {}
    if limited:
        user_src_list = user_sources(username)
        query["name"] = {'$in': user_src_list}
    if active:
        query['active'] = 'on'
    c = SourceAccess.objects(__raw__=query).order_by('+name')
    return c

def get_item_names(obj, active=None):
    """
    Get a list of item names for a specific item in CRITs.

    :param obj: The class representing the item to get names for.
    :type obj: class
    :param active: Return:
                   None: active and inactive items.
                   True: active items.
                   False: inactive items.
    :type active: boolean
    :returns: :class:`crits.core.crits_mongoengine.CritsQuerySet`
    """

    # Don't use this to get sources.
    if isinstance(obj, SourceAccess):
        return []

    if active is None:
       c = obj.objects().order_by('+name')
    else:
        if active:
            c = obj.objects(active='on').order_by('+name')
        else:
            c = obj.objects(active='off').order_by('+name')
    return c

def promote_bucket_list(bucket, confidence, name, related, description, analyst):
    """
    Promote a bucket to a Campaign. Every top-level object which is tagged with
    this specific bucket will get attributed to the provided campaign.

    :param bucket: The bucket to promote.
    :type bucket: str
    :param confidence: The Campaign confidence.
    :type confidence: str
    :param name: The Campaign name.
    :type name: str
    :param related: If we should extend this attribution to top-level objects
                    related to these top-level objects.
    :type related: boolean
    :param description: A description of this Campaign attribution.
    :type description: str
    :param analyst: The user promoting this bucket.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    from crits.campaigns.handlers import campaign_add

    bucket = Bucket.objects(name=bucket).first()
    if not bucket:
        return {'success': False, 'message': 'Unable to find bucket.'}

    for ctype in [k for k in Bucket._meta['schema_doc'].keys() if k != 'name' and k != 'Campaign']:
        # Don't bother if the count for this type is 0
        if getattr(bucket, ctype, 0) == 0:
            continue

        klass = class_from_type(ctype)
        if not klass:
            continue

        objs = klass.objects(bucket_list=bucket.name)
        for obj in objs:
            campaign_add(name, confidence, description, related, analyst, obj=obj)

    return {'success': True,
            'message': 'Bucket successfully promoted. <a href="%s">View campaign.</a>' % reverse('crits.campaigns.views.campaign_details', args=(name,))}

def alter_bucket_list(obj, buckets, val):
    """
    Given a list of buckets on this object, increment or decrement
    the bucket_list objects accordingly. This is used when adding
    or removing a bucket list to an item, and when deleting an item.

    :param obj: The top-level object instantiated class.
    :type obj: class which inherits from
               :class:`crits.core.crits_mongoengine.CritsBaseAttributes`.
    :param buckets: List of buckets.
    :type buckets: list
    :param val: The amount to change the count by.
    :type val: int
    """

    # This dictionary is used to set values on insert only.
    # I haven't found a way to get mongoengine to use the defaults
    # when doing update_one() on the queryset.
    from crits.core.bucket import Bucket
    soi = { k: 0 for k in Bucket._meta['schema_doc'].keys() if k != 'name' and k != obj._meta['crits_type'] }
    soi['schema_version'] = Bucket._meta['latest_schema_version']

    # We are using mongo_connector here because mongoengine does not have
    # support for a setOnInsert option. If mongoengine were to gain support
    # for this we should switch to using it instead of pymongo here.
    buckets_col = mongo_connector(settings.COL_BUCKET_LISTS)
    for name in buckets:
        buckets_col.update({'name': name},
                           {'$inc': {obj._meta['crits_type']: val},
                            '$setOnInsert': soi},
                           upsert=True)

        # Find and remove this bucket if, and only if, all counts are zero.
        if val == -1:
            Bucket.objects(name=name,
                           Actor=0,
                           Backdoor=0,
                           Campaign=0,
                           Certificate=0,
                           Domain=0,
                           Email=0,
                           Event=0,
                           Exploit=0,
                           Indicator=0,
                           IP=0,
                           PCAP=0,
                           RawData=0,
                           Sample=0,
                           Target=0).delete()

def generate_bucket_csv(request):
    """
    Generate CSV output for the Bucket list.

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    return csv_export(request, Bucket)

def generate_bucket_jtable(request, option):
    """
    Generate the jtable data for rendering in the bucket list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    if option == 'jtlist':
        details_url = 'crits.core.views.bucket_list'
        details_key = 'name'
        response = jtable_ajax_list(Bucket,
                                    details_url,
                                    details_key,
                                    request,
                                    includes=['name',
                                              'Actor',
                                              'Backdoor',
                                              'Campaign',
                                              'Certificate',
                                              'Domain',
                                              'Email',
                                              'Event',
                                              'Exploit',
                                              'Indicator',
                                              'IP',
                                              'PCAP',
                                              'RawData',
                                              'Sample',
                                              'Target'])
        return HttpResponse(json.dumps(response, default=json_handler),
                            content_type='application/json')

    fields = ['name', 'Actor', 'Backdoor', 'Campaign', 'Certificate', 'Domain',
              'Email', 'Event', 'Exploit', 'Indicator', 'IP', 'PCAP', 'RawData',
              'Sample', 'Target', 'Promote']
    jtopts = {'title': 'Buckets',
              'fields': fields,
              'listurl': 'jtlist',
              'searchurl': reverse('crits.core.views.global_search_listing'),
              'default_sort': 'name ASC',
              'no_sort': ['Promote'],
              'details_link': ''}
    jtable = build_jtable(jtopts, request)
    for ctype in fields:
        if ctype == 'id':
            continue
        elif ctype == 'name':
            url = reverse('crits.core.views.global_search_listing') + '?search_type=bucket_list&search=Search&force_full=1'
        elif ctype == 'Promote':
            url = reverse('crits.core.views.bucket_promote')
        else:
            lower = ctype.lower()
            if lower != "rawdata":
                url = reverse('crits.%ss.views.%ss_listing' % (lower, lower))
            else:
                lower = "raw_data"
                url = reverse('crits.%s.views.%s_listing' % (lower, lower))

        for field in jtable['fields']:
            if field['fieldname'].startswith("'" + ctype):
                if ctype == 'name':
                    field['display'] = """ function (data) {
                    return '<a href="%s&q='+encodeURIComponent(data.record.name)+'">' + data.record.name + '</a>';
                    }
                    """ % url
                elif ctype == 'Promote':
                    # This is really ugly. I don't know of a better way to
                    # use the campaign addition form and also submit name of
                    # the bucket. So the form is POSTed but the URL also
                    # has a bucket parameter that is for the name of the
                    # to operate on.
                    field['display'] = """ function (data) {
            return '<div class="icon-container"><span class="add_button" data-intro="Add a campaign" data-position="right"><a href="#" action="%s?name='+encodeURIComponent(data.record.name)+'" class="ui-icon ui-icon-plusthick dialogClick" dialog="campaign-add" persona="promote" title="Promote to campaign"></a></span></div>'
                    }
                    """ % url
                else:
                    field['display'] = """ function (data) {
                    return '<a href="%s?bucket_list='+encodeURIComponent(data.record.name)+'">'+data.record.%s+'</a>';
                    }
                    """ % (url, ctype)
    return render_to_response('bucket_lists.html',
                              {'jtable': jtable,
                               'jtid': 'bucket_lists'},
                              RequestContext(request))

def modify_bucket_list(itype, oid, tags, analyst):
    """
    Modify the bucket list for a top-level object.

    :param itype: The CRITs type of the top-level object to modify.
    :type itype: str
    :param oid: The ObjectId to search for.
    :type oid: str
    :param tags: The list of buckets.
    :type tags: list
    :param analyst: The user making the modifications.
    """

    obj = class_from_id(itype, oid)
    if not obj:
        return

    obj.add_bucket_list(tags, analyst, append=False)

    try:
        obj.save(username=analyst)
    except ValidationError:
        pass

def download_object_handler(total_limit, depth_limit, rel_limit, rst_fmt,
                            bin_fmt, object_types, objs, sources,
                            make_zip=True):
    """
    Given a list of tuples, collect the objects for each given the total
    number of objects to return for each, the depth to traverse for each
    and the maximum number of relationships to consider before ignoring.

    NOTE: This function can collect more than total_limit number of objects
    because total_limit applies only to each call to collect_objects() and
    not to the total number of things collected.

    :param total_limit: The max number of objects to return.
    :type total_limit: int
    :param depth_limit: The level of relationships to recurse into.
    :type depth_limit: int
    :param rel_limit: The limit on how many relationhips a top-level object
                      should have before we ignore its relationships.
    :type rel_limit: int
    :param rst_fmt: The format the results should be in ("zip", "stix",
                    "stix_no_bin").
    :type rst_fmt: str
    :param object_types: The types of top-level objects to include.
    :type object_types: list
    :param objs: A list of types (<obj_type>, <obj_id>) that we should use as
                 our basis to collect for downloading.
    :type objs: list
    :param sources: A list of sources to limit results against.
    :type sources: list
    :returns: A dict with the keys:
        "success" (boolean),
        "filename" (str),
        "data" (str),
        "mimetype" (str)
    """

    result = {'success': False}

    stix_docs = []
    to_zip = []
    need_filedata = rst_fmt != 'stix_no_bin'
    if not need_filedata:
        bin_fmt = None

    # If bin_fmt is not zlib or base64, force it to base64.
    if rst_fmt == 'stix' and bin_fmt not in ['zlib', 'base64']:
        bin_fmt = 'base64'

    for (obj_type, obj_id) in objs:
        # get related objects
        new_objects = collect_objects(obj_type, obj_id, depth_limit,
                                      total_limit, rel_limit, object_types,
                                      sources, need_filedata=need_filedata)

        # if result format calls for binary data to be zipped, loop over
        # collected objects and convert binary data to bin_fmt specified, then
        # add to the list of data to zip up
        for (oid, (otype, obj)) in new_objects.items():
            if ((otype == PCAP._meta['crits_type'] or
                 otype == Sample._meta['crits_type'] or
                 otype == Certificate._meta['crits_type']) and
               rst_fmt == 'zip'):
                if obj.filedata: # if data is available
                    if bin_fmt == 'raw':
                        to_zip.append((obj.filename, obj.filedata.read()))
                    else:
                        (data, ext) = format_file(obj.filedata.read(),
                                                  bin_fmt)
                        to_zip.append((obj.filename + ext, data))
                    obj.filedata.seek(0)
            else:
                try:
                    stix_docs.append(obj.to_stix(items_to_convert=[obj],
                                                loaded=True,
                                                bin_fmt=bin_fmt))
                except:
                    # Usually due to the object not being a supported exportable
                    # object such as Indicators with a type that is not a CybOX
                    # object.
                    pass

    doc_count = len(stix_docs)
    zip_count = len(to_zip)
    if doc_count == 1 and zip_count <= 0: # we have a single STIX doc to return
        result['success'] = True
        result['data'] = stix_docs[0]['stix_obj'].to_xml()
        result['filename'] = "%s_%s.xml" % (stix_docs[0]['final_objects'][0]._meta['crits_type'],
                                            stix_docs[0]['final_objects'][0].id)
        result['mimetype'] = 'text/xml'
    elif doc_count + zip_count >= 1: # we have multiple or mixed items to return
        if not make_zip:
            # We are making a single STIX document out of our results. Pop any
            # STIX object out of the list and use it as the "main" STIX object.
            # TODO: This fails miserably for Events since they are their own
            # unique STIX document.
            final_doc = stix_docs.pop()
            final_doc = final_doc['stix_obj']
            for doc in stix_docs:
                doc = doc['stix_obj']
                # Add any indicators from this doc into the "main" STIX object.
                if doc.indicators:
                    if isinstance(doc.indicators, list):
                        final_doc.indicators.extend(doc.indicators)
                    else:
                        final_doc.indicators.append(doc.indicators)
                # Add any observables from this doc into the "main" STIX object.
                if doc.observables:
                    if isinstance(doc.observables.observables, list):
                        for d in doc.observables.observables:
                            final_doc.observables.add(d)
                    else:
                        final_doc.observables.add(doc.observables)
                # Add any Actors from this doc into the "main" STIX object.
                if doc.threat_actors:
                    if isinstance(doc.threat_actors, list):
                        final_doc.threat_actors.extend(doc.threat_actors)
                    else:
                        final_doc.threat_actors.append(doc.threat_actors)
            # Convert the "main" STIX object into XML and return.
            result['success'] = True
            result['data'] = final_doc.to_xml()
            result['mimetype'] = 'application/xml'
        else:
            zip_data = to_zip
            for doc in stix_docs:
                inner_filename = "%s_%s.xml" % (doc['final_objects'][0]._meta['crits_type'],
                                                doc['final_objects'][0].id)
                zip_data.append((inner_filename, doc['stix_obj'].to_xml()))
            result['success'] = True
            result['data'] = create_zip(zip_data, True)
            result['filename'] = "CRITS_%s.zip" % datetime.datetime.today().strftime("%Y-%m-%d")
            result['mimetype'] = 'application/zip'
    return result

def collect_objects(obj_type, obj_id, depth_limit, total_limit, rel_limit,
                    object_types, sources, need_filedata=True, depth=0):
    """
    Collects an object from the database, along with its related objects, to
    the specified depth, or until the total limit is reached. This is a
    breadth first traversal because I think it's better to get objects as
    close to the initial one as possible, rather than traversing to the
    bottom of a tree first.

    If depth_limit is 0, relationships are not examined.

    If an object has too many relationships (configurable system wide)
    then it is ignored and that branch of the relationship tree is not
    taken.

    The returned object types will be only those in object_types. If
    a sample is found without a valid filedata attribute it will be
    collected only if need_fildata is False.

    Objects are returned as a dictionary with the following key/value
    mapping:
    _id: (obj_type, crits_obj)

    Sources should be a list of the names of the sources the user has
    permission to access.

    :param obj_type: The CRITs top-level object type to work with.
    :type obj_type: str
    :param obj_id: The ObjectId to search for.
    :type obj_id: str
    :param depth_limit: The level of relationships to recurse into.
    :type depth_limit: int
    :param total_limit: The max number of objects to return.
    :type total_limit: int
    :param rel_limit: The limit on how many relationhips a top-level object
                      should have before we ignore its relationships.
    :type rel_limit: int
    :param object_types: The types of top-level objects to include.
    :type object_types: list
    :param sources: A list of sources to limit results against.
    :type sources: list
    :param need_filedata: Include data from GridFS if applicable.
    :type need_filedata: boolean
    :param depth: Depth tracker. Default is 0 to start at no relationships and
                  work our way down.
    :returns: A dict with ObjectIds as keys, and values of tuples
              (<object_type>, <object>).
    """

    objects = {}

    # This dictionary is used to keep track of nodes that have been
    # seen already. This ensures that we do not circle back on the graph.
    seen_objects = {}

    def inner_collect(obj_type, obj, sources, depth, depth_limit, total_limit,
                      object_types, need_filedata):
        # Don't keep going if the total number of objects is reached.
        if len(objects) >= total_limit:
            return objects

        # Be cognizant of the need to collect samples with no backing binary
        # if the user asked for no binaries (need_filedata is False).
        #
        # If the object has a filedata attribute we need to collect it
        # if need_filedata is true and the filedata attribute is valid.
        # If the object does not have a valid filedata attribute and
        # need_filedata is False, then collect it (metadata only).
        #
        # If the object is not one we want to collect we will still traverse
        # down that path of the graph, but will not collect the object.
        if obj_type in object_types:
            if hasattr(obj, 'filedata'):
                if obj.filedata and need_filedata:
                    objects[obj.id] = (obj_type, obj)
                elif not need_filedata:
                    objects[obj.id] = (obj_type, obj)
            else:
                objects[obj.id] = (obj_type, obj)

        seen_objects[obj.id] = True

        # If not recursing (depth_limit == 0), return.
        # If at depth limit, return.
        if depth_limit == 0 or depth >= depth_limit:
            return objects

        new_objs = []
        for r in obj.relationships:
            # Don't touch objects we have already seen.
            if r.object_id in seen_objects:
                continue

            seen_objects[r.object_id] = True

            new_class = class_from_type(r.rel_type)
            if not new_class:
                continue

            new_obj = new_class.objects(id=str(r.object_id),
                                        source__name__in=sources).first()
            if not new_obj:
                continue

            # Don't go down this branch if there are too many relationships.
            # This most often happens when a common resource is extracted
            # from many samples.
            if len(new_obj.relationships) > rel_limit:
                continue

            # Save the objects so we can recurse into them later.
            new_objs.append((r.rel_type, new_obj))

            # Try to collect the new object, but don't handle relationships.
            # Do this by setting depth_limit to 0.
            inner_collect(r.rel_type, new_obj, sources, depth, 0, total_limit,
                          object_types, need_filedata)

        # Each of the new objects become a new starting point for traverse.
        depth += 1
        for (new_type, new_obj) in new_objs:
            inner_collect(new_type, new_obj, sources, depth, depth_limit,
                          total_limit, object_types, need_filedata)
        # END OF INNER COLLECT

    klass = class_from_type(obj_type)
    if not klass:
        return objects

    obj = klass.objects(id=str(obj_id), source__name__in=sources).first()
    if not obj:
        return objects

    inner_collect(obj_type, obj, sources, 0, depth_limit, total_limit,
                  object_types, need_filedata)

    return objects

def modify_source_access(analyst, data):
    """
    Update a user profile.

    :param analyst: The user to update.
    :type analyst: str
    :param data: The user profile fields to change and their values.
    :type data: dict
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    user = CRITsUser.objects(username=data['username']).first()
    if not user:
        user = CRITsUser.create_user(
            data.get('username', ''),
            data.get('password', ''),
            data.get('email') )
        if not user:
            return {'success': False,
                    'message': 'Missing user information username/password/email'}
    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.email = data['email']
    user.role = data['role']
    user.sources = data['sources']
    user.organization = data['organization']
    user.totp = data['totp']
    user.secret = data['secret']
    if len(data.get('password', '')) > 1:
        if user.set_password(data['password']) == False:
            config = CRITsConfig.objects().first()
            pc = config.password_complexity_desc
            return {'success': False,
                    'message': 'Password does not meet complexity policy: %s' % pc}
    if data['subscriptions'] == '':
        user.subscriptions = EmbeddedSubscriptions()
    try:
        user.save(username=analyst)
        return {'success': True}
    except ValidationError, e:
        return {'success': False,
                'message': format_error(e)}

def datetime_parser(d):
    """
    Iterate over a dictionary for any key of "date" and try to convert its value
    into a datetime object.

    :param d: A dictionary to iterate over.
    :type d: dict
    :returns: dict
    """

    for k,v in d.items():
        if k == "date":
            d[k] = datetime.datetime.strptime(v, settings.PY_DATETIME_FORMAT)
    return d

def format_error(e):
    """
    Takes an Exception and returns a nice string representation.

    :param e: An exception.
    :type e: Exception
    :returns: str
    """

    return e.__class__.__name__+": "+unicode(e)

def toggle_item_state(type_, oid, analyst):
    """
    Toggle an item active/inactive.

    :param type_: The CRITs type for this item.
    :type type_: str
    :param oid: The ObjectId to search for.
    :type oid: str
    :param analyst: The user toggling this item.
    :type analyst: str
    :returns: dict with key "success" (boolean)
    """

    obj = class_from_id(type_, oid)
    if not obj:
        return {'success': False}
    if obj.active == 'on':
        obj.active = 'off'
    else:
        obj.active = 'on'
    try:
        obj.save(username=analyst)
        return {'success': True}
    except ValidationError:
        return {'success': False}

def get_item_state(type_, name):
    """
    Get the state of an item.

    :param type_: The CRITs type for this item.
    :type type_: str
    :param name: The name of the item.
    :type name: str
    :returns: True if active, False if inactive.
    """

    if type_ == 'RelationshipType':
        query = {'forward': name}
    elif type_ == 'ObjectType':
        a = name.split(" - ")
        if len(a) == 1:
            query = {'name': name}
        else:
            query = {'type': a[0], 'name': a[1]}
    else:
        query = {'name': name}
    obj = class_from_type(type_).objects(__raw__=query).first()
    if not obj:
        return False
    if obj.active == 'on':
        return True
    else:
        return False

def remove_quotes(val):
    """
    Remove surrounding quotes from a string.

    :param val: The string to remove quotes from.
    :type val: str
    :returns: str
    """

    if val.startswith(('"', "'",)) and val.endswith(('"', "'",)):
        val = val[1:-1]
    return val

def generate_regex(val):
    """
    Takes the value, removes surrounding quotes, and generates a PyMongo $regex
    query for use on a field.

    :param val: The string to use for a regex.
    :type val: str
    :returns: dict with key '$regex' if successful, 'error' if failed.
    """

    try:
        return {'$regex': re.compile('%s' % remove_quotes(val), re.I)}
    except Exception, e:
        return {'error': 'Invalid Regular Expression: %s\n\n\t%s' % (val,
                                                                        str(e))}

def parse_search_term(term, force_full=False):
    """
    Parse a search term to break it into search operators that we can use to
    enhance the search results.

    :param term: Search term
    :type term: str
    :returns: search string or dictionary for regex search
    """

    # decode the term so we aren't dealing with weird encoded characters
    if force_full == False:
        term = urllib.unquote(term)
    # setup lexer, parse our term, and define operators
    sh = shlex.shlex(term.strip())
    sh.wordchars += '!@#$%^&*()-_=+[]{}|\:;<,>.?/~`'
    sh.commenters = ''
    parsed = list(iter(sh.get_token, ''))
    operators = ['regex', 'full', 'type', 'field']
    search = {}

    # for each parsed term, check to see if we have an operator and a value
    regex_term = ""
    if len(parsed) > 0:
        for p in parsed:
            s = p.split(':')
            if len(s) >= 2:
                so = s[0]
                st = ':'.join(s[1:])
                if so in operators:
                    # can make this more flexible for regex?
                    if so == 'regex':
                        search['query'] = generate_regex(st)
                    elif so == 'full':
                        regex_term += "%s " % (st,)
                        force_full = True
                    elif so == 'type':
                        search['type'] = st.title()
                    elif so == 'field':
                        search['field'] = remove_quotes(st.lower())
                else:
                    regex_term += "%s:%s " % (so, st)
            else:
                regex_term += "%s " % p
    if regex_term:
        if force_full:
            search['query'] = remove_quotes(regex_term.strip())
        else:
            search['query'] = generate_regex(regex_term.strip())
    return search

def gen_global_query(obj,user,term,search_type="global",force_full=False):
    """
    Generate a search query.  Also calls :func:`check_query` for validation.

    :param obj: CRITs Document Object
    :type obj: :class:`crits.core.crits_mongoengine.CritsDocument`
    :param user: CRITs user
    :type user: str
    :param term: Search term
    :type term: str
    :param search_type: Search type
    :type search_type: str
    :returns: dict -- The validated query dictionary
    """

    type_ = obj._meta['crits_type']
    search_list = []
    query = {}
    # Some terms, regardless of the query, will want to be full search terms and
    # not regex terms.
    force_full_terms = ['analysis_result', 'ssdeephash']
    force = False
    # Exclude searches for 'source' or 'releasability'
    # This is required because the check_query function doesn't handle
    # regex searches for these two fields
    if 'source' in search_type or 'releasability' in search_type:
        return query
    if search_type in force_full_terms or force_full != False:
        force = True
    parsed_search = parse_search_term(term, force_full=force)
    if 'query' not in parsed_search:
        return {'success': False,
                 'ignore': False,
                'error': 'No query to search'}
    if 'error' in parsed_search['query']:
        return {'success': False,
                 'ignore': False,
                'error': parsed_search['query']['error']}
    search_query = parsed_search['query']
    if 'type' in parsed_search:
        t = class_from_type(parsed_search['type'])
        if t:
            type_ = parsed_search['type']
            if obj._meta['crits_type'] != type_:
                return {'success': False,
                        'ignore': True,
                        'error': 'This type is being ignored.'}
    if 'field' in parsed_search:
        query = {parsed_search['field']: parsed_search['query']}
    defaultquery = check_query({search_type: search_query},user,obj)

    sample_queries = {
        'size' : {'size': search_query},
        'md5hash': {'md5': search_query},
        'sha1hash': {'sha1': search_query},
        'ssdeephash': {'ssdeep': search_query},
        'sha256hash': {'sha256': search_query},
        # slow in larger collections
        'filename': {'$or': [
            {'filename': search_query},
            {'filenames': search_query},
        ]},
        'campaign': {'campaign.name': search_query},
        # slightly slow in larger collections
        'object_value': {'objects.value': search_query},
        'bucket_list': {'bucket_list': search_query},
        'sectors': {'sectors': search_query},
        'source': {'source.name': search_query},
    }

    # if a specific field is being defined to search against, return early
    if 'field' in parsed_search:
        if 'filedata' in query:
            query = {'filedata': None}
        return query
    elif search_type == "bucket_list":
        query = {'bucket_list': search_query}
    elif search_type == "sectors":
        query = {'sectors': search_query}
    elif search_type == "actor_identifier":
        query = {'identifiers.identifier_id': search_query}
    # object_ comes from the core/views.py search function.
    # It joins search_type with otype
    elif search_type.startswith("object_"):
        if search_type == "object_value":
            query = {"objects.value": search_query}
        else:
            otypes = search_type.split("_")[1].split(" - ")
            if len(otypes) == 1:
                query = {"objects": {"$elemMatch": {"name": otypes[0],
                                                    "value": search_query}}}
            else:
                query = {"objects": {"$elemMatch": {"name": otypes[1],
                                                    "type": otypes[0],
                                                    "value": search_query}}}
    elif search_type == "byobject":
        query = {'comment': search_query}
    elif search_type == "global":
        if type_ == "Sample":
            search_list.append(sample_queries["object_value"])
            search_list.append(sample_queries["filename"])
            if len(term) == 32:
                search_list.append(sample_queries["md5hash"])
        elif type_ == "AnalysisResult":
            search_list = [
                    {'results.result': search_query},
            ]
        elif type_ == "Actor":
            search_list = [
                    {'name': search_query},
                    {'objects.value': search_query},
            ]
        elif type_ == "Certificate":
            search_list = [
                    {'md5': search_query},
                    {'objects.value': search_query},
                ]
        elif type_ == "PCAP":
            search_list = [
                    {'md5': search_query},
                    {'objects.value': search_query},
                ]
        elif type_ == "RawData":
            search_list = [
                    {'md5': search_query},
                    {'data': search_query},
                    {'objects.value': search_query},
                ]
        elif type_ == "Indicator":
            search_list = [
                    {'value': search_query},
                    {'objects.value': search_query}
                ]
        elif type_ == "Domain":
            search_list = [
                    {'domain': search_query},
                    {'objects.value': search_query}
                ]
        elif type_ == "Email":
            search_list = [
                    {'from': search_query},
                    {'subject': search_query},
                    {'raw_body': search_query},
                    {'raw_headers': search_query},
                    {'objects.value': search_query},
                    {'x_originating_ip': search_query},
                    {'originating_ip': search_query}
                ]
        elif type_ == "Event":
            search_list = [
                    {'description': search_query},
                    {'title': search_query},
                    {'objects.value': search_query}
                ]
        elif type_ == "IP":
            search_list = [
                    {'ip': search_query},
                    {'objects.value': search_query}
                ]
        elif type_ == "Comment":
            search_list = [
                    {'comment': search_query},
                ]
        elif type_ == "Campaign":
            search_list = [
                    {'name': search_query},
                    {'aliases': search_query},
                ]
        elif type_ == "Screenshot":
            search_list = [
                    {'description': search_query},
                    {'tags': search_query},
                ]
        elif type_ == "Target":
            search_list = [
                    {'email_address': search_query},
                    {'firstname': search_query},
                    {'lastname': search_query},
                ]
        else:
            search_list = [{'name': search_query}]
        search_list.append({'source.instances.reference':search_query})
        search_list.append({'bucket_list': search_query})
        search_list.append({'sectors': search_query})
        query = {'$or': search_list}
    else:
        if type_ == "Domain":
            query = {'domain': search_query}
        elif type_ == "Email":
            if search_type == "ip":
                query = {'$or': [{'originating_ip': search_query},
                                 {'x_originating_ip': search_query}]}
            elif search_type == "reference":
                query = {'source.instances.reference': search_query}
            else:
                query = defaultquery
        elif type_ == "RawData":
            if search_type == "data":
                query = {'data': search_query}
            elif search_type == "data_type":
                query = {'data_type': search_query}
            elif search_type == "title":
                query = {'title': search_query}
            elif search_type == "tool":
                query = {'tool.name': search_query}
            else:
                query = defaultquery
        elif type_ == "Event":
            if search_type == "campaign":
                query = {'campaign.name': search_query}
            elif search_type == "source":
                query = {'source.name': search_query}
            else:
                query = defaultquery
        elif type_ == "Indicator":
            if search_type == "campaign":
                query = {'campaign.name': search_query}
            elif search_type == "ticket_number":
                query = {'tickets.ticket_number': search_query}
            elif search_type == "source":
                query = {'source.name': search_query}
            elif search_type == "confidence":
                query = {'confidence.rating': search_query}
            elif search_type == "impact":
                query = {'impact.rating': search_query}
            else:
                query = defaultquery
        elif type_ == "IP":
            query = {'ip': search_query}
        elif type_ == "Sample":
            if search_type not in sample_queries:
                return {'success': None,
                        'ignore': False,
                        'error': 'Search type not in sample queries.'}
            query = sample_queries[search_type]
            if 'size' in query:
                try:
                    query = {'size': int(query['size'])}
                except ValueError:
                    return {'success': None,
                            'ignore': False,
                            'error': 'Size must be an integer.'}
        else:
            query = defaultquery

    return query

def check_query(qparams,user,obj):
    """
    Remove and/or filter queries which may cause issues

    :param qparams: MongoDB query
    :type qparams: dict
    :param user: CRITs user
    :type user: str
    :param obj: CRITs Document Object
    :type obj: :class:`crits.core.crits_mongoengine.CritsDocument`
    :returns: dict -- The validated query dictionary
    """

    # Iterate over the supplied query keys and make sure they start
    # with a valid field from the document
    goodkeys = {}
    for key,val in qparams.items():
        # Skip anything with Mongo's special $
        if '$' in key:
            continue
        # Grab the base field for doing the key checks
        try:
            indx = key.index('.')
            field = key[:indx]
        except:
            field = key
        # Check for mapping, reverse because we're going the other way
        invmap = dict((v,k) for k, v in obj._db_field_map.iteritems())
        if field in invmap:
            field = invmap[field]
        # Only allow query keys that exist in the object
        if hasattr(obj,field):
            goodkeys[key] = val

    # Filter out invalid queries regarding source/releasability
    sourcefilt = user_sources(user)
    newquery = goodkeys.copy()
    for key in goodkeys:
        # Sources
        if "source" in key:
            if key != "source.name" and key != "source":
                del newquery[key]
            else:
                if goodkeys[key] not in sourcefilt:
                    del newquery[key]
        # Releasability
        if "releasability" in key:
            if key != "releasability.name" and key != "releasability":
                del newquery[key]
            else:
                if goodkeys[key] not in sourcefilt:
                    del newquery[key]
    return newquery

def data_query(col_obj, user, limit=25, skip=0, sort=[], query={},
               projection=[], count=False):
    """
    Basic query function

    :param col_obj: MongoEngine collection object (Required)
    :type col_obj: :class:`crits.core.crits_mongoengine.CritsDocument`
    :param user: CRITs user (Required)
    :type user: str
    :param limit: Limit on returned rows
    :type limit: int `(25)`
    :param skip: Number of rows to skip
    :type skip: int `(0)`
    :param sort: Fields to sort by (Prepend field name with '-' to reverse sort)
    :type sort: list
    :param query: MongoDB query
    :type query: dict
    :param projection: Projection filter to apply to query
    :type projection: list
    :returns: dict -- Keys are result, data, count, msg, crits_type.  'data'
        contains a :class:`crits.core.crits_mongoengine.CritsQuerySet` object.
    """

    results = {'result':'ERROR'}
    results['data'] = []
    results['count'] = 0
    results['msg'] = ""
    results['crits_type'] = col_obj._meta['crits_type']
    sourcefilt = user_sources(user)
    if isinstance(sort,basestring):
        sort = sort.split(',')
    if isinstance(projection,basestring):
        projection = projection.split(',')
    docs = None
    try:
        if not issubclass(col_obj,CritsSourceDocument):
            results['count'] = col_obj.objects(__raw__=query).count()
            if count:
                results['result'] = "OK"
                return results
            if col_obj._meta['crits_type'] == 'User':
                docs = col_obj.objects(__raw__=query).exclude('password',
                                              'password_reset',
                                              'api_keys').\
                                              order_by(*sort).skip(skip).\
                                              limit(limit).only(*projection)
            else:
                docs = col_obj.objects(__raw__=query).order_by(*sort).\
                                    skip(skip).limit(limit).only(*projection)
        # Else, all other objects that have sources associated with them
        # need to be filtered appropriately
        else:
            results['count'] = col_obj.objects(source__name__in=sourcefilt,
                                               __raw__=query).count()
            if count:
                results['result'] = "OK"
                return results
            docs = col_obj.objects(source__name__in=sourcefilt,__raw__=query).\
                                    order_by(*sort).skip(skip).limit(limit).\
                                    only(*projection)
        for doc in docs:
            if hasattr(doc, "sanitize_sources"):
                doc.sanitize_sources(username="%s" % user, sources=sourcefilt)
    except Exception, e:
        results['msg'] = "ERROR: %s. Sort performed on: %s" % (e,
                                                               ', '.join(sort))
        return results
    results['data'] = docs
    results['result'] = "OK"
    return results

def csv_query(col_obj,user,fields=[],limit=10000,skip=0,sort=[],query={}):
    """
    Runs query and returns items in CSV format with fields as row headers

    :param col_obj: MongoEngine collection object (Required)
    :type col_obj: :class:`crits.core.crits_mongoengine.CritsDocument`
    :param user: CRITs user (Required)
    :type user: str
    :param fields: Fields to return in the CSV
    :type fields: list
    :param limit: Limit on returned rows
    :type limit: int
    :param skip: Number of rows to skip
    :type skip: int
    :param sort: Fields to sort by (Prepend field name with '-' to reverse sort)
    :type sort: list
    :param query: MongoDB query
    :type query: dict
    """

    results = data_query(col_obj, user=user, limit=limit,
                              skip=skip, sort=sort, query=query,
                              projection=fields)
    if results['result'] == "OK":
        return results['data'].to_csv(fields)
    else:
        return results['msg']

def parse_query_request(request,col_obj):
    """
    Get query modifiers from a request

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: dict -- Keys are fields, sort, limit, skip
    """

    resp = {}
    resp['fields'] = request.GET.get('fields',[])
    if resp['fields']:
        try:
            resp['fields'] = resp['fields'].split(',')
        except:
            return render_to_response("error.html",
                                          {"error": "Invalid fields specified"},
                                          RequestContext(request))
        goodfields = []
        for field in resp['fields']:
            # Skip anything with Mongo's special $
            if '$' in field:
                continue
            # Grab the base field for doing the key checks
            try:
                indx = field.index('.')
                base = field[:indx]
                extra = field[indx:]
            except:
                base = field
                extra = ""
            # Check for mapping, reverse because we're going the other way
            invmap = dict((v,k) for k, v in col_obj._db_field_map.iteritems())
            if base in invmap:
                base = invmap[base]
            # Only allow query keys that exist in the object
            if hasattr(col_obj,base):
                goodfields.append(base+extra)

        resp['fields'] = goodfields
    resp['sort'] = request.GET.get('sort',[])
    resp['limit'] = int(request.GET.get('limit',10000))
    resp['skip'] = int(request.GET.get('skip',0))
    return resp

def csv_export(request, col_obj, query={}):
    """
    Returns a :class:`django.http.HttpResponse` object which prompts the user
    to download a CSV file containing the results from :func:`csv_query`.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param col_obj: MongoEngine collection object (Required)
    :type col_obj: :class:`crits.core.crits_mongoengine.CritsDocument`
    :param query: MongoDB query
    :type query: dict
    :returns: :class:`django.http.HttpResponse` -- CSV download response
    """

    opts = parse_query_request(request,col_obj)
    if not query:
        resp = get_query(col_obj, request)
        if resp['Result'] == "ERROR":
            response = render_to_response("error.html",
                                          {"error": resp['Message'] },
                                          RequestContext(request)
                                          )
            return response
        query = resp['query']
    result = csv_query(col_obj, request.user.username, fields=opts['fields'],
                        sort=opts['sort'], query=query, limit=opts['limit'],
                        skip=opts['skip'])
    if isinstance(result, basestring):
        response = HttpResponse(result, content_type="text/csv")
        response['Content-Disposition'] = "attachment;filename=crits-%s-export.csv" % col_obj._meta['crits_type']
    else:
        response = render_to_response("error.html",
                                      {"error" : result },
                                      RequestContext(request))
    return response

def get_query(col_obj,request):
    """
    Pull out a query from a request object

    :param col_obj: MongoEngine collection object (Required)
    :type col_obj: :class:`crits.core.crits_mongoengine.CritsDocument`
    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: dict -- The MongoDB query
    """
    keymaps = {
            "actor_identifier": "identifiers.identifier_id",
            "campaign": "campaign.name",
            "source": "source.name",
            "confidence": "confidence.rating",
            "impact": "impact.rating",
            "object_value":"objects.value",
            "analysis_result":"results.result",
    }
    term = ""
    query = {}
    response = {}
    params_escaped = {}
    for k,v in request.GET.items():
        params_escaped[k] = html_escape(v)
    urlparams = "?%s" % urlencode(params_escaped)
    if "q" in request.GET:
        force_full = request.GET.get('force_full', False)
        term = request.GET.get('q')
        search_type = request.GET.get('search_type',None)
        if not search_type:
            response['Result'] = "ERROR"
            response['Message'] = "No search_type defined"
            return response
        otype = request.GET.get('otype', None)
        if otype:
            search_type = search_type + "_" + otype
        term = HTMLParser.HTMLParser().unescape(term)
        qdict = gen_global_query(col_obj,
                                 request.user.username,
                                 term,
                                 search_type,
                                 force_full=force_full
                                 )
        if not qdict.get('success', True):
            if qdict.get('ignore', False):
                response['Result'] = "IGNORE"
            else:
                response['Result'] = "ERROR"
            response['Message'] = qdict.get('error', 'Unable to process query')
            return response
        query.update(qdict)
        term = request.GET['q']
    qparams = request.REQUEST.copy()
    qparams = check_query(qparams,request.user.username,col_obj)
    for key,value in qparams.items():
        if key in keymaps:
            key = keymaps[key]

        # This one is not a straight rename like the others. If
        # searching for x_originating_ip also search for originating_ip,
        # and vice versa. This means we have to logically or the query
        # where the others do not.
        if key in ['x_originating_ip', 'originating_ip']:
            query["$or"] = [
                             {"x_originating_ip": value},
                             {"originating_ip": value}
                           ]
        elif key in ['size', 'length']:
            try:
                query[key] = int(value)
            except ValueError:
                results = {}
                results['Result'] = "ERROR"
                results['Message'] = "'size' requires integer, not %s" % value
                return results
        else:
            query[key] = value
        term = term + " " + value
    results = {}
    results['Result'] = "OK"
    results['query'] = query
    results['term'] = term
    results['urlparams'] = urlparams
    return results

def jtable_ajax_list(col_obj,url,urlfieldparam,request,excludes=[],includes=[],query={}):
    """
    Handles jTable listing POST requests

    :param col_obj: MongoEngine collection object (Required)
    :type col_obj: :class:`crits.core.crits_mongoengine.CritsDocument`
    :param url: Base URL for objects. Ex ``crits.domains.views.domain_detail``
    :type url: str
    :param urlfieldparam: Field to use for the item detail's URL key.  Passed
        as arg with ``url`` to :func:`django.core.urlresolvers.reverse`
    :type urlfieldparam: str
    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param excludes: Fields to exclude
    :type excludes: list
    :param includes: Fields to include
    :type includes: list
    :param query: MongoDB query
    :type query: dict
    """

    response = {"Result": "ERROR"}
    users_sources = user_sources(request.user.username)
    if request.is_ajax():
        pageSize = request.user.get_preference('ui','table_page_size',25)

        # Thought these were POSTs...GET works though
        skip = int(request.GET.get("jtStartIndex", "0"))
        if "jtLimit" in request.GET:
            pageSize = int(request.GET['jtLimit'])
        else:
            pageSize = int(request.GET.get("jtPageSize", pageSize))

        # Set the sort order
        sort = request.GET.get("jtSorting", urlfieldparam+" ASC")
        keys = sort.split(',')
        multisort = []

        keymaps = {
            "actor_identifier": "identifiers.identifier_id",
            "campaign": "campaign.name",
            "source": "source.name",
            "confidence": "confidence.rating",
            "impact": "impact.rating",
            "object_value": "objects.value",
            "analysis_result": "results.result",
        }

        for key in keys:
            (keyname, keyorder) = key.split()
            if keyname in keymaps:
                keyname = keymaps[keyname]
            if keyorder == "DESC":
                keyname = "-%s" % keyname
            multisort.append(keyname)

        # Build the query
        term = ""
        if not query:
            resp = get_query(col_obj, request)
            if resp['Result'] in ["ERROR", "IGNORE"]:
                return resp
            query = resp['query']
            term = resp['term']

        response = data_query(col_obj, user=request.user.username, limit=pageSize,
                              skip=skip, sort=multisort, query=query,
                              projection=includes)
        if response['result'] == "ERROR":
            return {'Result': "ERROR", 'Message': response['msg']}
        response['crits_type'] = col_obj._meta['crits_type']
        # Escape term for rendering in the UI.
        response['term'] = cgi.escape(term)
        response['data'] = response['data'].to_dict(excludes, includes)
        # Convert data_query to jtable stuff
        response['Records'] = response.pop('data')
        response['TotalRecordCount'] = response.pop('count')
        response['Result'] = response.pop('result')
        for doc in response['Records']:
            for key, value in doc.items():
                # all dates should look the same
                if isinstance(value, datetime.datetime):
                    doc[key] = datetime.datetime.strftime(value,
                                                          "%Y-%m-%d %H:%M:%S")
                if key == "password_reset":
                    doc['password_reset'] = None
                if key == "campaign":
                    camps = []
                    for campdict in value:
                        camps.append(campdict['name'])
                    doc[key] = "|||".join(camps)
                elif key == "source":
                    srcs = []
                    for srcdict in doc[key]:
                        if srcdict['name'] in users_sources:
                            srcs.append(srcdict['name'])
                    doc[key] = "|||".join(srcs)
                elif key == "tags":
                    tags = []
                    for tag in doc[key]:
                        tags.append(tag)
                    doc[key] = "|||".join(tags)
                elif key == "is_active":
                    if value:
                        doc[key] = "True"
                    else:
                        doc[key] = "False"
                elif key == "datatype":
                    doc[key] = value.keys()[0]
                elif key == "results":
                    doc[key] = len(doc[key])
                elif isinstance(value, list):
                    if value:
                        for item in value:
                            if not isinstance(item, basestring):
                                break
                        else:
                            doc[key] = ",".join(value)
                    else:
                        doc[key] = ""
                if key != urlfieldparam:
                    doc[key] = html_escape(doc[key])
            if col_obj._meta['crits_type'] == "Comment":
                mapper = {
                    "Actor": 'crits.actors.views.actor_detail',
                    "Campaign": 'crits.campaigns.views.campaign_details',
                    "Certificate": 'crits.certificates.views.certificate_details',
                    "Domain": 'crits.domains.views.domain_detail',
                    "Email": 'crits.emails.views.email_detail',
                    "Event": 'crits.events.views.view_event',
                    "Indicator": 'crits.indicators.views.indicator',
                    "IP": 'crits.ips.views.ip_detail',
                    "PCAP": 'crits.pcaps.views.pcap_details',
                    "RawData": 'crits.raw_data.views.raw_data_details',
                    "Sample": 'crits.samples.views.detail',
                }
                doc['url'] = reverse(mapper[doc['obj_type']],
                                    args=(doc['url_key'],))
            elif col_obj._meta['crits_type'] == "AuditLog":
                if doc.get('method', 'delete()') != 'delete()':
                    doc['url'] = details_from_id(doc['type'],
                                                 doc.get('target_id', None))
            elif not url:
                doc['url'] = None
            else:
                doc['url'] = reverse(url, args=(unicode(doc[urlfieldparam]),))
    return response

def jtable_ajax_delete(obj,request):
    """
    Delete a document specified in the jTable POST.

    :param obj: MongoEngine collection object (Required)
    :type obj: :class:`crits.core.crits_mongoengine.CritsDocument`
    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: bool -- True if item was deleted
    """

    # Only admins can delete
    if not is_admin(request.user.username):
        return False
    # Make sure we are supplied _id
    if not "id" in request.POST:
        return False
    docid = request.POST['id']
    if not docid:
        return False
    # Finally, make sure there is a related document
    doc = obj.objects(id=docid).first()
    if not doc:
        return False
    if "delete_all_relationships" in dir(doc):
        doc.delete_all_relationships()
    # For samples/pcaps
    if "filedata" in dir(doc):
        doc.filedata.delete()
    doc.delete(username=request.user.username)
    return True

def build_jtable(jtopts, request):
    """
    Build a dictionary containing proper jTable options.

    :param jtopts: Python dictionary containing jTable options.
    :type jtopts: dict.
    :param request: Current Django request
    :type request: :class:`django.http.HttpRequest`
    :returns: dict -- Contains the jTable configuration used by the template.

    **jtopts supports the following keys**
        **Required**
            *title*
                Contains the jTable title.
            *listurl*
                URL for the Django view that returns the data in JSON.
            *searchurl*
                URL to use when filtering data, usually the base URL for the view,
                without any options.
            *fields*
                Python list containing the fields to show for a document.  The
                first item will be linked to the details view.

        **Optional**
            *default_sort*
                Defines the field and order to sort by.
                    Ex. "field <ASC|DESC>"
                    Default: FirstField ASC

            *deleteurl*
                URL for Django view to delete an item
            *no_sort*
                Python list containing which fields to disable sorting
            *hidden_fields*
                Python list containing which fields to hide.  This list is a
                subset of 'fields'
            *linked_fields*
                Python list containing which fields should allow filtering.
            *paging*
                Allow paging on this jTable.
                    Default: true
            *pageSize*
                Number of rows per page
                   Deafult: User Preference (defaults to 25)
            *sorting*
                Allow sorting by column on this jTable
                    Default: true
            *multiSorting*
                Allow sorting by multiple columns on this jTable
                    Default: true
            *details_link*
                Define the field that should link to the details
                    Default: First field
                    If specified as '__disable__', then no linking will occur
                    If specified as 'details', an icon is used for the link

    """

    # Check for required values
    if not all(required in jtopts for required in ['listurl','searchurl','fields','title']):
        raise KeyError("Missing required key for jtopts in build_jtable")
        return None

    # jTable requires a key for the field
    # Mongo provides _id as a unique identifier, so we will require that
    if "id" not in jtopts['fields']:
        jtopts['fields'].append("id")
        # If we push the _id field on, we will also hide it by default
        if 'hidden_fields' in jtopts:
            jtopts['hidden_fields'].append("id")
        else:
            jtopts['hidden_fields'] = ["id",]


    pageSize = request.user.get_preference('ui','table_page_size',25)

    # Default jTable options
    default_options = {
        "paging" : "true",
        "pageSize": pageSize,
        "sorting": "true",
        "multiSorting": "true",
    }

    # Default widths for certain columns in the jTable
    colwidths = {
        "details": "'2%'",
        'recip': "'2%'",
        "comment":"'15%'",
        "date":"'8%'",
        "isodate":"'8%'",
        "id":"'4%'",
        "favorite":"'4%'",
        "size":"'4%'",
        "added":"'8%'",
        "created":"'8%'",
        "modified":"'8%'",
        "subject":"'17%'",
        "value":"'18%'",
        "type":"'10%'",
        "filetype":"'15%'",
        "status":"'5%'",
        "source":"'7%'",
        "campaign":"'7%'",
    }

    # Mappings for the column titles
    titlemaps = {
        "Isodate": "Date",
        "Created": "Added",
        "Ip": "IP",
        "Id": "Store ID",
    }

    jtable = {}
    # This allows overriding of default options if they are specified in jtopts
    for defopt,defval in default_options.items():
        if defopt in jtopts:
            jtable[defopt] = jtopts[defopt]
        else:
            jtable[defopt] = defval

    # Custom options
    if 'title' in jtopts:
        jtable['title'] = jtopts['title']
    else:
        jtable['title'] = ""
    jtable['defaultSorting'] = jtopts['default_sort']


    # Define jTable actions
    jtable['actions'] = {}
    # List action
    # If we have get parameters, append them
    if request.GET:
        jtable['actions']['listAction'] = jtopts['listurl'] + "?"+request.GET.urlencode(safe='@')
    else:
        jtable['actions']['listAction'] = jtopts['listurl']

    # Delete action
    # If user is admin and deleteurl is set, provide a delete action in jTable
    if ( is_admin(request.user.username) and
            'deleteurl' in jtopts and jtopts['deleteurl'] ):
        jtable['actions']['deleteAction'] = jtopts['deleteurl']

    # We don't have any views available for these actions
    #jtable['actions']['createAction'] = reverse()
    #jtable['actions']['updateAction'] = reverse()

    # Generate the fields
    jtable['fields'] = []

    for field in jtopts['fields']:
        fdict = {}

        # Create the column title here
        title = field.replace("_"," ").title().strip()
        if title in titlemaps:
            title = titlemaps[title]
        # Some options require quotes, so we use "'%s'" to quote them
        fdict['title'] = "'%s'" % title

        fdict['fieldname'] = "'%s'" % field
        if field in colwidths:
            fdict['width'] = colwidths[field]
        # Every jTable needs a key.  All our items in Mongo have a unique _id
        # identifier, so by default we always include that here as the key
        if field == "id":
            fdict['key'] = "true"
            fdict['display'] = """function (data) { return '<div class="icon-container"><span id="'+data.record.id+'" class="id_copy ui-icon ui-icon-copy"></span></div>';}"""
        if field == "favorite":
            fdict['display'] = """function (data) { return '<div class="icon-container"><span id="'+data.record.id+'" class="favorites_icon_jtable ui-icon ui-icon-star"></span></div>';}"""
        if field == "thumb":
            fdict['display'] = """function (data) { return '<img src="%s'+data.record.id+'/thumb/" />';}""" % reverse('crits.screenshots.views.render_screenshot')
        if field == "description" and jtable['title'] == "Screenshots":
            fdict['display'] = """function (data) { return '<span class="edit_underline edit_ss_description" data-id="'+data.record.id+'">'+data.record.description+'</span>';}"""
        if 'no_sort' in jtopts and field in jtopts['no_sort']:
            fdict['sorting'] = "false"
        if 'hidden_fields' in jtopts and field in jtopts['hidden_fields']:
            # hide the row but allow the user to show it
            fdict['visibility'] = '"hidden"'
        # This creates links for certain jTable columns
        # It will link anything listed in 'linked_fields'
        campbase = reverse('crits.campaigns.views.campaign_details',args=('__CAMPAIGN__',))

        # If linked_fields is not specified lets link source and campaign
        # if they exist as fields in the jTable
        if 'linked_fields' not in jtopts:
            jtopts['linked_fields'] = []
            if 'source' in jtopts['fields']:
                jtopts['linked_fields'].append("source")
            if 'campaign' in jtopts['fields']:
                jtopts['linked_fields'].append("campaign")
        if field in jtopts['linked_fields']:
            fdict['display'] = """function (data) {
                return link_jtable_column(data, '%s', '%s', '%s');
            } """ % (field, jtopts['searchurl'], campbase)

        jtable['fields'].append(fdict)
    if 'details_link' in jtopts:
        if jtopts['details_link'] == "__disabled__":
            return jtable
        else:
            if jtopts['details_link'] not in jtopts['fields']:
                return jtable
            # Link the field in details_link
            linkfield = "'%s'" % jtopts["details_link"]
            for i,field in enumerate(jtable['fields']):
                if field['fieldname'] != linkfield:
                    continue
                if field['fieldname'] == "'details'":
                    jtable['fields'][i]['display'] = 'function (data) {if (!data.record.url) { return '';}; return \'<a href="\'+data.record.url+\'" target="_parent"><div class="icon-container"><span class="ui-icon ui-icon-document" title="View Details"></span></div></a>\';}'
                else:
                    jtable['fields'][i]['display'] = "function (data) {return '<a href=\"'+data.record.url+'\">'+data.record."+jtopts['fields'][i]+"+'</a>';}"
    else:
        # Provide default behavior
        if jtable['fields'][0]['fieldname'] == "'details'":
            jtable['fields'][0]['display'] = 'function (data) {return \'<a href="\'+data.record.url+\'"><div class="icon-container"><span class="ui-icon ui-icon-document" title="View Details"></span></div></a>\';}'
        else:
            jtable['fields'][0]['display'] = "function (data) {return '<a href=\"'+data.record.url+'\">'+data.record."+jtopts['fields'][0]+"+'</a>';}"
    return jtable

def generate_items_jtable(request, itype, option):
    """
    Generate a jtable list for the Item provided.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param itype: The CRITs item we want to list.
    :type itype: str
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = class_from_type(itype)

    if itype == 'ActorThreatIdentifier':
        fields = ['name', 'active', 'id']
        click = "function () {window.parent.$('#actor_identifier_type_add').click();}"
    elif itype == 'ActorThreatType':
        fields = ['name', 'active', 'id']
    elif itype == 'ActorMotivation':
        fields = ['name', 'active', 'id']
    elif itype == 'ActorSophistication':
        fields = ['name', 'active', 'id']
    elif itype == 'ActorIntendedEffect':
        fields = ['name', 'active', 'id']
    elif itype == 'Campaign':
        fields = ['name', 'description', 'active', 'id']
        click = "function () {window.parent.$('#new-campaign').click();}"
    elif itype == 'EventType':
        fields = ['name', 'active', 'id']
    elif itype == 'IndicatorAction':
        fields = ['name', 'active', 'id']
        click = "function () {window.parent.$('#indicator_action_add').click();}"
    elif itype == 'ObjectType':
        fields = ['name', 'name_type', 'object_type', 'datatype', 'description',
                  'active', 'id']
    elif itype == 'RawDataType':
        fields = ['name', 'active', 'id']
        click = "function () {window.parent.$('#raw_data_type_add').click();}"
    elif itype == 'RelationshipType':
        fields = ['forward', 'reverse', 'description', 'active', 'id']
    elif itype == 'SourceAccess':
        fields = ['name', 'active', 'id']
        click = "function () {window.parent.$('#source_create').click();}"
    elif itype == 'UserRole':
        fields = ['name', 'active', 'id']
        click = "function () {window.parent.$('#user_role').click();}"

    if option == 'jtlist':
        details_url = None
        details_url_key = 'name'
        response = jtable_ajax_list(obj_type, details_url, details_url_key,
                                    request, includes=fields)
        return HttpResponse(json.dumps(response, default=json_handler),
                            content_type="application/json")

    if itype == "ObjectType":
        fields = ['name', 'name_type', 'type', 'datatype', 'description',
                  'active', 'id']

    jtopts = {
        'title': "%ss" % itype,
        'default_sort': 'name ASC',
        'listurl': reverse('crits.core.views.items_listing',
                           args=(itype, 'jtlist',)),
        'deleteurl': None,
        'searchurl': None,
        'fields': fields,
        'hidden_fields': ['id'],
        'linked_fields': [],
        'details_link': '',
    }
    jtable = build_jtable(jtopts, request)
    if itype not in ('ActorThreatType', 'ActorMotivation',
                     'ActorSophistication', 'ActorIntendedEffect',
                     'EventType', 'ObjectType', 'RelationshipType'):
        jtable['toolbar'] = [
            {
                'tooltip': "'Add %s'" % itype,
                'text': "'Add %s'" % itype,
                'click': click,
            },
        ]

    for field in jtable['fields']:
        if field['fieldname'].startswith("'active"):
            field['display'] = """ function (data) {
            return '<a id="is_active_' + data.record.id + '" href="#" onclick=\\'javascript:toggleItemActive("%s","'+data.record.id+'");\\'>' + data.record.active + '</a>';
            }
            """ % itype
    if option == "inline":
        return render_to_response("jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%ss_listing' % itype.lower(),
                                   'button': '%ss_tab' % itype.lower()},
                                  RequestContext(request))
    else:
        return render_to_response("item_editor.html",
                                  {'jtable': jtable,
                                   'jtid': 'items_listing'},
                                  RequestContext(request))

def generate_users_jtable(request, option):
    """
    Generate a jtable list for Users.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = CRITsUser
    if option == 'jtlist':
        details_url = None
        details_url_key = 'username'
        fields = ['username', 'first_name', 'last_name', 'email',
                   'last_login', 'organization', 'role', 'is_active',
                   'id']
        excludes = ['login_attempts']
        response = jtable_ajax_list(obj_type, details_url, details_url_key,
                                    request, includes=fields,
                                    excludes=excludes)
        return HttpResponse(json.dumps(response, default=json_handler),
                            content_type="application/json")
    jtopts = {
        'title': "Users",
        'default_sort': 'username ASC',
        'listurl': reverse('crits.core.views.users_listing', args=('jtlist',)),
        'deleteurl': None,
        'searchurl': None,
        'fields': ['username', 'first_name', 'last_name', 'email',
                   'last_login', 'organization', 'role', 'is_active',
                   'id'],
        'hidden_fields': ['id'],
        'linked_fields': []
    }
    jtable = build_jtable(jtopts, request)
    jtable['toolbar'] = [
        {
            'tooltip': "'Add User'",
            'text': "'Add User'",
            'click': "function () {editUser('');}",
        },

    ]

    for field in jtable['fields']:
        if field['fieldname'].startswith("'username"):
            field['display'] = """ function (data) {
            return '<a class="user_edit" href="#" onclick=\\'javascript:editUser("'+data.record.username+'");\\'>' + data.record.username + '</a>';
            }
            """
        if field['fieldname'].startswith("'is_active"):
            field['display'] = """ function (data) {
            return '<a id="is_active_' + data.record.username + '" href="#" onclick=\\'javascript:toggleUserActive("'+data.record.username+'");\\'>' + data.record.is_active + '</a>';
            }
            """
    if option == "inline":
        return render_to_response("jtable.html",
                                  {'jtable': jtable,
                                   'jtid': 'users_listing'},
                                  RequestContext(request))
    else:
        return render_to_response("user_editor.html",
                                  {'jtable': jtable,
                                   'jtid': 'users_listing'},
                                  RequestContext(request))

def generate_dashboard(request):
    """
    Generate the Dashboard.
    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """
    from crits.dashboards.handlers import get_dashboard
    args = get_dashboard(request.user)
    return render_to_response('dashboard.html', args, RequestContext(request))

def dns_timeline(query, analyst, sources):
    """
    Query for domains, format that data for timeline view, and return them.

    :param query: The query to use to find the Domains.
    :type query: dict
    :param analyst: The user requesting the timeline.
    :type analyst: str
    :param sources: List of user's sources.
    :type sources: list
    :returns: list of dictionaries.
    """

    domains = Domain.objects(__raw__=query)
    offline = ['255.255.255.254', '127.0.0.1', '127.0.0.2', '0.0.0.0']
    event_id = 0
    events = []
    for d in domains:
        d.sanitize_sources(username=analyst,
                           sources=sources)
        domain = d.domain
        state = "off"
        ip_list = [r for r in d.relationships if r.rel_type == 'IP']
        ip_list = sorted(ip_list, key=itemgetter('relationship_date'), reverse=False)
        description = ""
        e = {}
        for ipl in ip_list:
            ip = IP.objects(ip=ipl.object_id,
                            source__name__in=sources).first()
            if ipl['relationship_date'] is None:
                continue
            e['id'] = event_id
            e['date_display'] = "hour"
            e['importance'] = 20
            e['icon'] = "halfcircle_blue.png"
            event_id += 1
            if ip and ip.ip in offline:
                if state == "on":
                    e['enddate'] = datetime.datetime.strftime(ipl['relationship_date'],
                                                            settings.PY_DATETIME_FORMAT)
                    e['description'] = description
                    state = "off"
                    events.append(e)
                    description = ""
                    e = {}
                elif state == "off":
                    pass
            elif ip:
                if state == "on":
                    description += "<br /><b><a style=\"display: inline;\" href=\"%s\">%s</a>:</b> %s" % (reverse('crits.ips.views.ip_detail', args=[ip.ip]), ip.ip, ipl['relationship_date'])
                elif state == "off":
                    e['startdate'] = datetime.datetime.strftime(ipl['relationship_date'],
                                                                settings.PY_DATETIME_FORMAT)
                    e['title'] = domain
                    description += "<br /><b><a style=\"display: inline;\" href=\"%s\">%s</a>:</b> %s" % (reverse('crits.ips.views.ip_detail', args=[ip.ip]), ip.ip, ipl['relationship_date'])
                    state = "on"
    return events

def email_timeline(query, analyst, sources):
    """
    Query for emails, format that data for timeline view, and return them.

    :param query: The query to use to find the Emails.
    :type query: dict
    :param analyst: The user requesting the timeline.
    :type analyst: str
    :param sources: List of user's sources.
    :type sources: list
    :returns: list of dictionaries.
    """

    emails = Email.objects(__raw__=query)
    events = []
    event_id = 0
    for email in emails:
        email.sanitize_sources(username=analyst,
                                sources=sources)
        email = email.to_dict()
        if "source" in email and email["source"][0] is not None:
            e = {}
            e['title'] = ""
            e['id'] = event_id
            e['date_display'] = "hour"
            e['importance'] = 20
            e['icon'] = "halfcircle_blue.png"
            event_id += 1
            if "from" in email:
                if email["from"]:
                    e['title'] += email["from"]
            if "campaign" in email:
                try:
                    if "name" in email["campaign"][0]:
                        e['title'] += " (%s)" % email["campaign"][0]["name"]
                except:
                    pass
            if "source" in email:
                if "name" in email["source"][0]:
                    e['title'] += " (%s)" % email["source"][0]["name"]
            description = ""
            sources = []
            if "from" in email:
                description += "<br /><b>%s</b>: <a style=\"display: inline;\" href=\"%s\">%s</a>" % \
                               (email["from"],
                                reverse('crits.emails.views.email_detail', args=[email['_id']]),
                                email["from"])
            if "isodate" in email:
                e['startdate'] = "%s" % email["isodate"]
            else:
                if "source" in email:
                    e['startdate'] = "%s" % email["source"][0]['instances'][0]["date"]
            if "source" in email:
                description += "<br /><hr><b>Source:</b>"
                for source in email["source"]:
                    if "name" in source and "instances" in source:
                        description += "<br /><b>%s</b>: %s" % (source["name"],
                                                                source['instances'][0]["date"])
            e['description'] = description
            events.append(e)
    return events

def indicator_timeline(query, analyst, sources):
    """
    Query for indicators, format that data for timeline view, and return them.

    :param query: The query to use to find the Indicators.
    :type query: dict
    :param analyst: The user requesting the timeline.
    :type analyst: str
    :param sources: List of user's sources.
    :type sources: list
    :returns: list of dictionaries.
    """

    indicators = Indicator.objects(__raw__=query)
    events = []
    event_id = 0
    for indicator in indicators:
        indicator.sanitize_sources(username=analyst,
                                   sources=sources)
        indicator = indicator.to_dict()
        e = {}
        e['title'] = indicator['value']
        e['id'] = event_id
        e['date_display'] = "hour"
        e['importance'] = 20
        e['icon'] = "halfcircle_blue.png"
        event_id += 1
        e['startdate'] = indicator['created'].strftime("%Y-%m-%d %H:%M:%S.%Z")
        description = ""
        description += "<br /><b>Value</b>: <a style=\"display: inline;\" href=\"%s\">%s</a>" % (reverse('crits.indicators.views.indicator', args=[indicator['_id']]), indicator['value'])
        description += "<br /><b>Type</b>: %s" % indicator['type']
        description += "<br /><b>Created</b>: %s" % indicator['created']
        e['description'] = description
        events.append(e)
    return events

def generate_user_profile(username, request):
    """
    Generate the user profile page.

    :param username: The user profile to generate.
    :type username: str
    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    user_source_access = user_sources(username)
    user_source_access.sort()
    limit = 5

    user_info = CRITsUser.objects(username=username).first()
    if not user_info:
        return {"status": "ERROR", "message": "User not found"}

    # recent indicators worked on
    query = {'$or': [{'actions.analyst': "%s" % username},
                     {'activity.analyst': "%s" % username},
                     {'objects.analyst': "%s" % username}]}
    indicator_list = (Indicator.objects(__raw__=query)
                      .only('value',
                            'ind_type',
                            'created',
                            'campaign',
                            'source',
                            'status')
                      .order_by('-created')
                      .limit(limit)
                      .sanitize_sources(username))

    # recent emails worked on
    query = {'campaign.analyst': "%s" % username}
    email_list = (Email.objects(__raw__=query)
                  .order_by('-date')
                  .limit(limit)
                  .sanitize_sources(username))

    # samples
    sample_md5s = (AuditLog.objects(user=username,
                                    target_type="Sample")
                   .order_by('-date')
                   .limit(limit))
    md5s = []
    for sample in sample_md5s:
        md5s.append(sample.value.split(" ")[0])
    filter_data = ('md5', 'source', 'filename', 'mimetype',
                   'size', 'campaign')
    sample_list = (Sample.objects(md5__in=md5s)
                   .only(*filter_data)
                   .sanitize_sources(username))

    subscriptions = user_info.subscriptions
    subscription_count = 0

    # collect subscription information
    if 'Sample' in subscriptions:
        subscription_count += len(subscriptions['Sample'])
        final_samples = []
        ids = [ObjectId(s['_id']) for s in subscriptions['Sample']]
        samples = Sample.objects(id__in=ids).only('md5', 'filename')
        m = map(itemgetter('_id'), subscriptions['Sample'])
        for sample in samples:
            s = sample.to_dict()
            s['md5'] = sample['md5']
            s['id'] = sample.id
            s['date'] = subscriptions['Sample'][m.index(sample.id)]['date']
            final_samples.append(s)
        subscriptions['Sample'] = final_samples

    if 'PCAP' in subscriptions:
        subscription_count += len(subscriptions['PCAP'])
        final_pcaps = []
        ids = [ObjectId(s['_id']) for s in subscriptions['PCAP']]
        pcaps = PCAP.objects(id__in=ids).only('md5', 'filename')
        m = map(itemgetter('_id'), subscriptions['PCAP'])
        for pcap in pcaps:
            p = pcap.to_dict()
            p['id'] = pcap.id
            p['date'] = subscriptions['PCAP'][m.index(pcap.id)]['date']
            final_pcaps.append(p)
        subscriptions['PCAP'] = final_pcaps

    if 'Email' in subscriptions:
        subscription_count += len(subscriptions['Email'])
        final_emails = []
        ids = [ObjectId(s['_id']) for s in subscriptions['Email']]
        emails = Email.objects(id__in=ids).only('from_address',
                                                'sender',
                                                'subject')
        m = map(itemgetter('_id'), subscriptions['Email'])
        for email in emails:
            e = email.to_dict()
            e['id'] = email.id
            e['date'] = subscriptions['Email'][m.index(email.id)]['date']
            final_emails.append(e)
        subscriptions['Email'] = final_emails

    if 'Indicator' in subscriptions:
        subscription_count += len(subscriptions['Indicator'])
        final_indicators = []
        ids = [ObjectId(s['_id']) for s in subscriptions['Indicator']]
        indicators = Indicator.objects(id__in=ids).only('value', 'ind_type')
        m = map(itemgetter('_id'), subscriptions['Indicator'])
        for indicator in indicators:
            i = indicator.to_dict()
            i['id'] = indicator.id
            i['date'] = subscriptions['Indicator'][m.index(indicator.id)]['date']
            final_indicators.append(i)
        subscriptions['Indicator'] = final_indicators

    if 'Event' in subscriptions:
        subscription_count += len(subscriptions['Event'])
        final_events = []
        ids = [ObjectId(s['_id']) for s in subscriptions['Event']]
        events = Event.objects(id__in=ids).only('title', 'description')
        m = map(itemgetter('_id'), subscriptions['Event'])
        for event in events:
            e = event.to_dict()
            e['id'] = event.id
            e['date'] = subscriptions['Event'][m.index(event.id)]['date']
            final_events.append(e)
        subscriptions['Event'] = final_events

    if 'Domain' in subscriptions:
        subscription_count += len(subscriptions['Domain'])
        final_domains = []
        ids = [ObjectId(s['_id']) for s in subscriptions['Domain']]
        domains = Domain.objects(id__in=ids).only('domain')
        m = map(itemgetter('_id'), subscriptions['Domain'])
        for domain in domains:
            d = domain.to_dict()
            d['id'] = domain.id
            d['date'] = subscriptions['Domain'][m.index(domain.id)]['date']
            final_domains.append(d)
        subscriptions['Domain'] = final_domains

    if 'IP' in subscriptions:
        subscription_count += len(subscriptions['IP'])
        final_ips = []
        ids = [ObjectId(s['_id']) for s in subscriptions['IP']]
        ips = IP.objects(id__in=ids).only('ip')
        m = map(itemgetter('_id'), subscriptions['IP'])
        for ip in ips:
            i = ip.to_dict()
            i['id'] = ip.id
            i['date'] = subscriptions['IP'][m.index(ip.id)]['date']
            final_ips.append(i)
        subscriptions['IP'] = final_ips

    if 'Campaign' in subscriptions:
        subscription_count += len(subscriptions['Campaign'])
        final_campaigns = []
        ids = [ObjectId(s['_id']) for s in subscriptions['Campaign']]
        campaigns = Campaign.objects(id__in=ids).only('name')
        m = map(itemgetter('_id'), subscriptions['Campaign'])
        for campaign in campaigns:
            c = campaign.to_dict()
            c['id'] = campaign.id
            c['date'] = subscriptions['Campaign'][m.index(campaign.id)]['date']
            final_campaigns.append(c)
        subscriptions['Campaign'] = final_campaigns

    # Collect favorite information
    favorites = user_info.favorites.to_dict()
    collected_favorites = {}
    total_favorites = 0
    for type_ in favorites.keys():
        ids = [ObjectId(i) for i in favorites[type_]]
        if ids:
            count = class_from_type(type_).objects(id__in=ids).count()
        else:
            count = 0
        total_favorites += count
        url = reverse('crits.core.views.favorites_list', args=(type_, 'inline'))
        collected_favorites[type_] = {
                                       'count': count,
                                       'url': url
                                     }

    #XXX: this can be removed after jtable
    notifications = get_user_notifications(username)

    result = {'username': username,
              'user_info': user_info,
              'user_sources': user_source_access,
              'indicators': indicator_list,
              'emails': email_list,
              'favorites': collected_favorites,
              'total_favorites': total_favorites,
              'notifications': notifications,
              'samples': sample_list,
              'subscriptions': subscriptions,
              'subscription_count': subscription_count,
              'ui_themes': ui_themes(),
              'rt_url': settings.RT_URL}

    result['preferences'] = generate_user_preference(request)

    return result

def generate_favorites_jtable(request, type_, option):
    """
    Generate favorites jtable.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param type_: The type of CRITs object.
    :type type_: str
    :returns: :class:`django.http.HttpResponse`
    """

    klass = class_from_type(type_)
    mapper = klass._meta['jtable_opts']
    if option == "jtlist":
        # Sets display url
        details_url = mapper['details_url']
        details_url_key = mapper['details_url_key']
        fields = mapper['fields']

        user = CRITsUser.objects(username=request.user.username).only('favorites').first()
        favorites = user.favorites.to_dict()
        ids = [ObjectId(s) for s in favorites[type_]]
        query = {'_id': {'$in': ids}}

        response = jtable_ajax_list(klass,
                                    details_url,
                                    details_url_key,
                                    request,
                                    includes=fields,
                                    query=query)
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")

    jtopts = {
        'title': type_ + 's',
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits.core.views.favorites_list', args=(type_, 'jtlist')),
        'searchurl': reverse(mapper['searchurl']),
        'fields': mapper['jtopts_fields'],
        'hidden_fields': mapper['hidden_fields'],
        'linked_fields': mapper['linked_fields'],
        'details_link': mapper['details_link'],
        'no_sort': mapper['no_sort']
    }

    jtable = build_jtable(jtopts, request)

    if option == "inline":
        return render_to_response("jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_,
                                   'button' : '%ss_tab' % type_},
                                  RequestContext(request))
    else:
        return render_to_response("%s_listing.html" % type_,
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_},
                                  RequestContext(request))

def generate_user_preference(request,section=None,key=None,name=None):
    """
    Generate user preferences.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param section: The section of the preferences to return.
    :type section: str
    :param key: The specific preference field within the section
                to be retrieved.
    :type key: str
    :param name: The section of the preferences to return.
    :type name: This is used to differentiate between different
                preference under the same "section" and "key".
                Otherwise the first "section" name that matches will
                be returned. For example there may be two
                different "notify" sections and also
                two different "toggle" keys. But the "key" matching
                the "name" value will be returned.
    :returns: list
    """

    # Returned as an array to maintain the order
    # could also have a key/value and a ordered array

    from crits.core.forms import PrefUIForm, NavMenuForm, ToastNotificationConfigForm

    toast_notifications_title = "Toast Notifications"

    config = CRITsConfig.objects().first()
    if not config.enable_toasts:
        toast_notifications_title += " (currently globally disabled by an admin)"

    preferences = [
        {'section': 'notify',
         'title': 'Notifications',
         'toggle': 'email',
         'enabled': get_user_email_notification(request.user.username),
         'name': 'Email Notifications'
         },
        {'section': 'toast_notifications',
         'title': toast_notifications_title,
         'form': ToastNotificationConfigForm(request),
         'formclass': ToastNotificationConfigForm,
        },
        {'section': 'ui',
         'title': 'UI Settings',
         'form': PrefUIForm(request),
         'formclass': PrefUIForm,
         'reload': True },

        {'section': 'nav',
         'form': NavMenuForm(request),
         'formclass': NavMenuForm,
         'name': 'Navigation Menu',
         'title': 'Navigation Menu',
         'reload': True },
        ]

    # Only return the requested section as hash
    if section:
        for pref in preferences:
            if key:
                if pref['section'] == section and pref[key] == name:
                    return pref
            else:
                if pref['section'] == section:
                    return pref

    return preferences

def reset_user_password(username=None, action=None, email=None,
                        submitted_rcode=None, new_p=None, new_p_c=None,
                        analyst=None):
    """
    Handle the process of resetting a user's password.

    :param username: The user resetting their password.
    :type username: str
    :param action: What action we need to take:
                   - send_email: sends email to user with reset code
                   - submit_reset_code: validate the reset code
                   - submit_passwords: reset the password
    :type action: str
    :param email: The user's email address.
    :type email: str
    :param submitted_rcode: The reset code submitted by the user.
    :type submitted_rcode: str
    :param new_p: The new password provided by the user.
    :type new_p: str
    :param new_p_c: The new password confirmation provided by the user.
    :type new_p_c: str
    :param analyst: The user submitting these changes.
    :type analyst: str
    :returns: :class:`django.http.HttpResponse`
    """

    if action not in ('send_email', 'submit_reset_code', 'submit_passwords'):
        response = {'success': False, 'message': 'Invalid action'}
        return HttpResponse(json.dumps(response, default=json_handler),
                            content_type="application/json")
    user = CRITsUser.objects(username=username, email=email).first()
    if not user:
        # make it seem like this worked even if it didn't to prevent people
        # from brute forcing usernames and email addresses.
        response = {'success': True, 'message': 'Instructions sent to %s' % email}
        return HttpResponse(json.dumps(response, default=json_handler),
                            content_type="application/json")
    if action == 'send_email':
        rcode = user.set_reset_code(analyst)
        crits_config = CRITsConfig.objects().first()
        if crits_config.crits_email_end_tag:
            subject = "CRITs Password Reset" + crits_config.crits_email_subject_tag
        else:
            subject = crits_config.crits_email_subject_tag + "CRITs Password Reset"
        body = """You are receiving this email because someone has requested a
password reset for your account. If it was not you, please log
into CRITs immediately which will remove the reset code from your
account. If it was you, here is your reset code:\n\n
"""
        body += "%s\n\n" % rcode
        body += """You have five minutes to reset your password before this
reset code expires.\n\nThank you!
"""
        user.email_user(subject, body)
        response = {'success': True, 'message': 'Instructions sent to %s' % email}
        return HttpResponse(json.dumps(response, default=json_handler),
                            content_type="application/json")
    if action == 'submit_reset_code':
        return HttpResponse(json.dumps(user.validate_reset_code(submitted_rcode,
                                                                analyst),
                                        default=json_handler),
                            content_type="application/json")
    if action == 'submit_passwords':
        return HttpResponse(json.dumps(user.reset_password(submitted_rcode,
                                                            new_p, new_p_c,
                                                           analyst),
                                        default=json_handler),
                            content_type="application/json")

def login_user(username, password, next_url=None, user_agent=None,
               remote_addr=None, accept_language=None, request=None,
               totp_pass=None):
    """
    Handle the process of authenticating a user.

    :param username: The user authenticating to the system.
    :type username: str
    :param password: The password provided by the user.
    :type password: str
    :param next_url: The URL to redirect to after successful login.
    :type next_url: str
    :param user_agent: The user-agent of the request.
    :type user_agent: str
    :param remote_addr: The remote-address of the request.
    :type remote_addr: str
    :param accept_language: The accept-language of the request.
    :type accept_language: str
    :param request: The request.
    :type request: :class:`django.http.HttpRequest`
    :param totp_pass: The TOTP password provided by the user.
    :type totp_pass: str
    :returns: dict with keys:
              "success" (boolean),
              "type" (str) - Type of failure,
              "message" (str)
    """

    error = 'Unknown user or bad password.'
    response = {}
    crits_config = CRITsConfig.objects().first()
    if not crits_config:
        response['success'] = False
        response['type'] = "login_failed"
        response['message'] = error
        return response

    if request:
        totp = crits_config.totp_web
    else:
        totp = crits_config.totp_cli

    # Do the username and password authentication
    # TOTP is passed here so that authenticate() can check if
    # the threshold has been exceeded.
    user = authenticate(username=username,
                        password=password,
                        user_agent=user_agent,
                        remote_addr=remote_addr,
                        accept_language=accept_language,
                        totp_enabled=totp)

    if user:
        if totp == 'Required' or (totp == 'Optional' and user.totp):
            # Remote user auth'd but has not seen TOTP screen yet
            if crits_config.remote_user and not totp_pass:
                response['success'] = False
                response['type'] = "totp_required"
                response['message'] = "TOTP required"
                return response
            e = EmbeddedLoginAttempt(user_agent=user_agent,
                                     remote_addr=remote_addr,
                                     accept_language=accept_language)
            secret = user.secret
            if not secret and not totp_pass:
                response['success'] = False
                response['type'] = "no_secret"
                response['message'] = ("You have no TOTP secret. Please enter "
                                       "a new PIN in the TOTP field.")
                return response
            elif not secret and totp_pass:
                response['success'] = False
                response['type'] = "secret_generated"
                res = save_user_secret(username, totp_pass, "crits", (200,200))
                if res['success']:
                    user.reload()
                    secret = res['secret']
                    if not request:
                        response['secret'] = secret
                        return response
                    message = "Setup your authenticator using: '%s'" % secret
                    message += "<br />Then authenticate again with your PIN + token."
                    if res['qr_img']:
                        message += '<br /><img src="data:image/png;base64,'
                        message += '%s" />' % res['qr_img']
                    response['message'] = message
                else:
                    response['message'] = "Secret Generation Failed"
                return response
            elif not valid_totp(username, totp_pass, secret):
                e.success = False
                user.login_attempts.append(e)
                user.invalid_login_attempts += 1
                user.save()
                response['success'] = False
                response['type'] = "login_failed"
                response['message'] = error
                return response
            e.success = True
            user.login_attempts.append(e)
            user.save()
        if user.is_active:
            user.invalid_login_attempts = 0
            user.password_reset.reset_code = ""
            user.save()
            if crits_config and request:
                request.session.set_expiry(crits_config.session_timeout * 60 * 60)
            elif request:
                request.session.set_expiry(settings.SESSION_TIMEOUT)
            if request:
                user_login(request, user)
            response['type'] = "login_successful"
            # Redirect to next or default dashboard
            if next_url is not None and next_url != '' and next_url != 'None':
                try:
                    # test that we can go from URL to view to URL
                    # to validate the URL is something we know about.
                    # We use get_script_prefix() here to tell us what
                    # the script prefix is configured in Apache.
                    # We strip it out so resolve can work properly, and then
                    # redirect to the full url.
                    prefix = get_script_prefix()
                    tmp_url = next_url
                    if next_url.startswith(prefix):
                        tmp_url = tmp_url.replace(prefix, '/', 1)
                    res = resolve(tmp_url)
                    url_name = res.url_name
                    args = res.args
                    kwargs = res.kwargs
                    redir = reverse(url_name, args=args, kwargs=kwargs)
                    del redir
                    response['success'] = True
                    response['message'] = next_url
                except:
                    response['success'] = False
                    response['message'] = 'ALERT - attempted open URL redirect attack to %s. Please report this to your system administrator.' % next_url
                return response
            response['success'] = True
            if 'message' not in response:
                response['message'] = reverse('crits.dashboards.views.dashboard')
            return response
        else:
            logger.info("Attempted login to a disabled account detected: %s" %
                        user.username)

    response['success'] = False
    response['type'] = "login_failed"
    response['message'] = error
    return response

def generate_global_search(request):
    """
    Generate global search results.

    :param request: The request.
    :type request: :class:`django.http.HttpRequest`
    :returns: dict with keys:
              "url_params" (str),
              "term" (str) - the search term,
              "results" (list),
              "Result" (str of "OK" or "ERROR")
    """
    # Perform rapid search for ObjectID strings
    searchtext = request.GET['q']
    if ObjectId.is_valid(searchtext):
        for obj_type, url, key in [
                ['Actor', 'crits.actors.views.actor_detail', 'id'],
                ['Backdoor', 'crits.backdoors.views.backdoor_detail', 'id'],
                ['Campaign', 'crits.campaigns.views.campaign_details', 'name'],
                ['Certificate', 'crits.certificates.views.certificate_details', 'md5'],
                ['Domain', 'crits.domains.views.domain_detail', 'domain'],
                ['Email', 'crits.emails.views.email_detail', 'id'],
                ['Event', 'crits.events.views.view_event', 'id'],
                ['Exploit', 'crits.exploits.views.exploit_detail', 'id'],
                ['Indicator', 'crits.indicators.views.indicator', 'id'],
                ['IP', 'crits.ips.views.ip_detail', 'ip'],
                ['PCAP', 'crits.pcaps.views.pcap_details', 'md5'],
                ['RawData', 'crits.raw_data.views.raw_data_details', 'id'],
                ['Sample', 'crits.samples.views.detail', 'md5'],
                ['Target', 'crits.targets.views.target_info', 'email_address']]:
            obj = class_from_id(obj_type, searchtext)
            if obj:
                return {'url': url, 'key': obj[key]}

    # Importing here to prevent a circular import with Services and runscript.
    from crits.services.analysis_result import AnalysisResult

    results = []
    for col_obj,url in [
                    [Actor, "crits.actors.views.actors_listing"],
                    [AnalysisResult, "crits.services.views.analysis_results_listing"],
                    [Backdoor, "crits.backdoors.views.backdoors_listing"],
                    [Campaign, "crits.campaigns.views.campaigns_listing"],
                    [Certificate, "crits.certificates.views.certificates_listing"],
                    [Comment, "crits.comments.views.comments_listing"],
                    [Domain, "crits.domains.views.domains_listing"],
                    [Email, "crits.emails.views.emails_listing"],
                    [Event, "crits.events.views.events_listing"],
                    [Exploit, "crits.exploits.views.exploits_listing"],
                    [Indicator,"crits.indicators.views.indicators_listing"],
                    [IP, "crits.ips.views.ips_listing"],
                    [PCAP, "crits.pcaps.views.pcaps_listing"],
                    [RawData, "crits.raw_data.views.raw_data_listing"],
                    [Sample, "crits.samples.views.samples_listing"],
                    [Screenshot, "crits.screenshots.views.screenshots_listing"],
                    [Target, "crits.targets.views.targets_listing"]]:
        ctype = col_obj._meta['crits_type']
        resp = get_query(col_obj, request)
        if resp['Result'] == "ERROR":
            return resp
        elif resp['Result'] == "IGNORE":
            results.append({'count': 0,
                            'url': url,
                            'name': ctype})
        else:
            formatted_query = resp['query']
            term = resp['term']
            urlparams = resp['urlparams']

            resp = data_query(col_obj, request.user.username, query=formatted_query, count=True)
            results.append({'count': resp['count'],
                            'url': url,
                            'name': ctype})
    return {'url_params': urlparams,
            'term': term,
            'results': results,
            'Result': "OK"}

def download_grid_file(request, dtype, sample_md5):
    """
    Download a file from GriDFS. The file will get zipped up.

    This should go away and get roped into our other download feature.

    :param request: The request.
    :type request: :class:`django.http.HttpRequest`
    :param dtype: 'pcap', 'object', or 'cert'.
    :type dtype: str
    :param sample_md5: The MD5 of the file to download.
    :type sample_md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    if dtype == 'object':
        grid = mongo_connector("%s.files" % settings.COL_OBJECTS)
        obj = grid.find_one({'md5': sample_md5})
        if obj is None:
            dtype = 'pcap'
        else:
            data = [(obj['filename'], get_file(sample_md5, "objects"))]
            zip_data = create_zip(data, False)
            response = HttpResponse(zip_data, mimetype='application/octet-stream')
            response['Content-Disposition'] = 'attachment; filename=%s' % obj['filename'] + ".zip"
            return response
    if dtype == 'pcap':
        pcaps = mongo_connector(settings.COL_PCAPS)
        pcap = pcaps.find_one({"md5": sample_md5})
        if not pcap:
            return render_to_response('error.html',
                                      {'data': request,
                                       'error': "File not found."},
                                      RequestContext(request))
        data = [(pcap['filename'], get_file(sample_md5, "pcaps"))]
        zip_data = create_zip(data, False)
        response = HttpResponse(zip_data, mimetype='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=%s' % pcap['filename'] + ".zip"
        return response
    if dtype == 'cert':
        certificates = mongo_connector(settings.COL_CERTIFICATES)
        cert = certificates.find_one({"md5": sample_md5})
        if not cert:
            return render_to_response('error.html',
                                      {'data': request,
                                       'error': "File not found."},
                                      RequestContext(request))
        data = [(cert['filename'], get_file(sample_md5, "certificates"))]
        zip_data = create_zip(data, False)
        response = HttpResponse(zip_data, mimetype='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=%s' % cert['filename'] + ".zip"
        return response


def generate_counts_jtable(request, option):
    """
    Generate the jtable data for counts.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "jtlist":
        count = mongo_connector(settings.COL_COUNTS)
        counts = count.find_one({'name': 'counts'})
        response = {}
        response['Result'] = "OK"
        response['Records'] = []
        if counts:
            for k, v in sorted(counts['counts'].items()):
                record = {}
                record['type'] = k
                record['count'] = v
                record['id'] = 0
                record['url'] = ""
                response['Records'].append(record)
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    else:
        return render_to_response('error.html',
                                  {'data': request,
                                   'error': "Invalid request"},
                                  RequestContext(request))


def generate_audit_jtable(request, option):
    """
    Generate the jtable data for audit log entries.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = AuditLog
    type_ = "audit"
    if option == "jtlist":
        # Sets display url
        details_url = 'crits.core.views.details'
        details_url_key = "target_id"
        response = jtable_ajax_list(obj_type,
                                    details_url,
                                    details_url_key,
                                    request)
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    jtopts = {
        'title': "Audit Log Entries",
        'default_sort': "date DESC",
        'listurl': reverse('crits.core.views.%s_listing' % type_,
                           args=('jtlist',)),
        'deleteurl': '',
        'searchurl': reverse('crits.core.views.%s_listing' % type_),
        'fields': ["details",
                   "user",
                   "type",
                   "method",
                   "value",
                   "date",
                   "id"],
        'hidden_fields': ["id"],
        'linked_fields': [],
        'details_link': 'details',
        'no_sort': ['details', ],
    }
    jtable = build_jtable(jtopts, request)
    jtable['toolbar'] = []
    if option == "inline":
        return render_to_response("jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_,
                                   'button': '%ss_tab' % type_},
                                  RequestContext(request))
    else:
        return render_to_response("%s_listing.html" % type_,
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_},
                                  RequestContext(request))


def details_from_id(type_, id_):
    """
    Determine the details URL based on type and ID and redirect there.

    :param type_: The CRITs type to search for.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :returns: str
    """

    type_map = {'Actor': 'crits.actors.views.actor_detail',
                'Backdoor': 'crits.backdoors.views.backdoor_detail',
                'Campaign': 'crits.campaigns.views.campaign_details',
                'Certificate': 'crits.certificates.views.certificate_details',
                'Domain': 'crits.domains.views.domain_detail',
                'Email': 'crits.emails.views.email_detail',
                'Event': 'crits.events.views.view_event',
                'Exploit': 'crits.exploits.views.exploit_detail',
                'Indicator': 'crits.indicators.views.indicator',
                'IP': 'crits.ips.views.ip_detail',
                'PCAP': 'crits.pcaps.views.pcap_details',
                'RawData': 'crits.raw_data.views.raw_data_details',
                'Sample': 'crits.samples.views.detail',
                'Screenshot': 'crits.screenshots.views.render_screenshot',
                'Target': 'crits.targets.views.target_info',
                }
    if type_ in type_map and id_:
        if type_ == 'Campaign':
            arg = class_from_id(type_, id_)
            if arg:
                arg = arg.name
        elif type_ == 'Certificate':
            arg = class_from_id(type_, id_)
            if arg:
                arg = arg.md5
        elif type_ == 'Domain':
            arg = class_from_id(type_, id_)
            if arg:
                arg = arg.domain
        elif type_ == 'IP':
            arg = class_from_id(type_, id_)
            if arg:
                arg = arg.ip
        elif type_ == 'PCAP':
            arg = class_from_id(type_, id_)
            if arg:
                arg = arg.md5
        elif type_ == 'Sample':
            arg = class_from_id(type_, id_)
            if arg:
                arg = arg.md5
        elif type_ == 'Target':
            arg = class_from_id(type_, id_)
            if arg:
                arg = arg.email_address
        else:
            arg = id_

        if not arg:
            return None

        return reverse(type_map[type_], args=(arg,))
    else:
        return None

def audit_entry(self, username, type_, new_doc=False):
    """
    Generate an audit entry.

    :param self: The object.
    :type self: class which inherits from
                :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param username: The user performing the action.
    :type username: str
    :param type_: The type of action being performed ("save", "delete").
    :type type_: str
    :param new_doc: If this is a new document being added to the database.
    :type new_doc: boolean
    """

    if username is None:
        # If no username, skip the audit log
        return

    my_type = self._meta['crits_type']
    # don't audit audits
    if my_type in ("AuditLog", "Service"):
        return
    changed_fields = [f.split('.')[0] for f in self._get_changed_fields() if f not in ("modified",
                                                                  "save",
                                                                  "delete")]

    # Remove any duplicate fields
    changed_fields = list(set(changed_fields))

    if new_doc and not changed_fields:
        what_changed = "new document"
    else:
        what_changed = ', '.join(changed_fields)

    key_descriptor = key_descriptor_from_obj_type(my_type)

    if key_descriptor is not None:
        value = getattr(self, key_descriptor, '')
    else:
        value = ""

    if type_ == "save":
        a = AuditLog()
        a.user = username
        a.target_type = my_type
        a.target_id = self.id
        a.value = what_changed
        a.method = "save()"
        try:
            a.save()
        except ValidationError:
            pass
    elif type_ == "delete":
        a = AuditLog()
        a.user = username
        a.target_type = my_type
        a.target_id = self.id
        a.value = value
        a.method = "delete()"
        try:
            a.save()
        except ValidationError:
            pass

    # Generate audit notification
    generate_audit_notification(username, type_, self, changed_fields, what_changed, new_doc)

def ticket_add(type_, id_, ticket):
    """
    Add a ticket to a top-level object.

    :param type_: The CRITs type of the top-level object.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :param ticket: The ticket to add.
    :type ticket: dict with keys "analyst", "date", and "ticket_number".
    :returns: dict with keys:
              "success" (boolean),
              "object" (str) if successful,
              "message" (str) if failed.
    """

    obj = class_from_id(type_, id_)
    if not obj:
        return {'success': False, 'message': 'Could not find object.'}

    try:
        obj.add_ticket(ticket['ticket_number'],
                             ticket['analyst'],
                             ticket['date'])
        obj.save(username=ticket['analyst'])
        return {'success': True, 'object': ticket}
    except ValidationError, e:
        return {'success': False, 'message': e}

def ticket_update(type_, id_, ticket):
    """
    Update a ticket for a top-level object.

    :param type_: The CRITs type of the top-level object.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :type ticket: dict with keys "analyst", "date", and "ticket_number".
    :type ticket: str
    :returns: dict with keys:
              "success" (boolean),
              "object" (str) if successful,
              "message" (str) if failed.
    """

    obj = class_from_id(type_, id_)
    if not obj:
        return {'success': False, 'message': 'Could not find object.'}

    try:
        obj.edit_ticket(ticket['analyst'],
                        ticket['ticket_number'],
                        ticket['date'])
        obj.save(username=ticket['analyst'])
        return {'success': True, 'object': ticket}
    except ValidationError, e:
        return {'success': False, 'message': e}

def ticket_remove(type_, id_, date, analyst):
    """
    Remove a ticket from a top-level object.

    :param type_: The CRITs type of the top-level object.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :param date: The date of the ticket to remove.
    :type date: datetime.datetime.
    :param analyst: The user removing the ticket.
    :type analyst: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str) if failed.
    """

    obj = class_from_id(type_, id_)
    if not obj:
        return {'success': False, 'message': 'Could not find object.'}

    try:
        obj.delete_ticket(date)
        obj.save(username=analyst)
        return {'success': True}
    except ValidationError, e:
        return {'success': False, 'message': e}

def unflatten(dictionary):
    """
    Unflatten a dictionary.

    :param dictionary: The dictionary to unflatten.
    :type dictionary: dict
    :returns: dict
    """

    resultDict = dict()
    for key, value in dictionary.iteritems():
        parts = key.split(".")
        d = resultDict
        for part in parts[:-1]:
            if part not in d:
                d[part] = dict()
            d = d[part]
        d[parts[-1]] = value
    return resultDict

def alter_sector_list(obj, sectors, val):
    """
    Given a list of sectors on this object, increment or decrement
    the sectors objects accordingly. This is used when adding
    or removing a sector list to an item, and when deleting an item.

    :param obj: The top-level object instantiated class.
    :type obj: class which inherits from
               :class:`crits.core.crits_mongoengine.CritsBaseAttributes`.
    :param sectors: List of sectors.
    :type sectors: list
    :param val: The amount to change the count by.
    :type val: int
    """

    # This dictionary is used to set values on insert only.
    # I haven't found a way to get mongoengine to use the defaults
    # when doing update_one() on the queryset.
    soi = { k: 0 for k in Sector._meta['schema_doc'].keys() if k != 'name' and k != obj._meta['crits_type'] }
    soi['schema_version'] = Sector._meta['latest_schema_version']

    # We are using mongo_connector here because mongoengine does not have
    # support for a setOnInsert option. If mongoengine were to gain support
    # for this we should switch to using it instead of pymongo here.
    sectors_col = mongo_connector(settings.COL_SECTOR_LISTS)
    for name in sectors:
        sectors_col.update({'name': name},
                           {'$inc': {obj._meta['crits_type']: val},
                            '$setOnInsert': soi},
                           upsert=True)

        # Find and remove this sector if, and only if, all counts are zero.
        if val == -1:
            Sector.objects(name=name,
                           Actor=0,
                           Campaign=0,
                           Certificate=0,
                           Domain=0,
                           Email=0,
                           Event=0,
                           Indicator=0,
                           IP=0,
                           PCAP=0,
                           RawData=0,
                           Sample=0,
                           Target=0).delete()

def generate_sector_csv(request):
    """
    Generate CSV output for the Sector list.

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    return csv_export(request, Sector)

def generate_sector_jtable(request, option):
    """
    Generate the jtable data for rendering in the sector list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    if option == 'jtlist':
        details_url = 'crits.core.views.sector_list'
        details_key = 'name'
        response = jtable_ajax_list(Sector,
                                    details_url,
                                    details_key,
                                    request,
                                    includes=['name',
                                              'Actor',
                                              'Backdoor',
                                              'Campaign',
                                              'Certificate',
                                              'Domain',
                                              'Email',
                                              'Event',
                                              'Exploit',
                                              'Indicator',
                                              'IP',
                                              'PCAP',
                                              'RawData',
                                              'Sample',
                                              'Target'])
        return HttpResponse(json.dumps(response, default=json_handler),
                            content_type='application/json')

    fields = ['name', 'Actor', 'Backdoor', 'Campaign', 'Certificate', 'Domain',
              'Email', 'Event', 'Exploit', 'Indicator', 'IP', 'PCAP', 'RawData',
              'Sample', 'Target']
    jtopts = {'title': 'Sectors',
              'fields': fields,
              'listurl': 'jtlist',
              'searchurl': reverse('crits.core.views.global_search_listing'),
              'default_sort': 'name ASC',
              'no_sort': [],
              'details_link': ''}
    jtable = build_jtable(jtopts, request)
    for ctype in fields:
        if ctype == 'id':
            continue
        elif ctype == 'name':
            url = reverse('crits.core.views.global_search_listing') + '?search_type=sectors&search=Search&force_full=1'
        else:
            lower = ctype.lower()
            if lower != "rawdata":
                url = reverse('crits.%ss.views.%ss_listing' % (lower, lower))
            else:
                lower = "raw_data"
                url = reverse('crits.%s.views.%s_listing' % (lower, lower))

        for field in jtable['fields']:
            if field['fieldname'].startswith("'" + ctype):
                if ctype == 'name':
                    field['display'] = """ function (data) {
                    return '<a href="%s&q='+encodeURIComponent(data.record.name)+'">' + data.record.name + '</a>';
                    }
                    """ % url
                else:
                    field['display'] = """ function (data) {
                    return '<a href="%s?sectors='+encodeURIComponent(data.record.name)+'">'+data.record.%s+'</a>';
                    }
                    """ % (url, ctype)
    return render_to_response('sector_lists.html',
                              {'jtable': jtable,
                               'jtid': 'sector_lists'},
                              RequestContext(request))

def modify_sector_list(itype, oid, sectors, analyst):
    """
    Modify the sector list for a top-level object.

    :param itype: The CRITs type of the top-level object to modify.
    :type itype: str
    :param oid: The ObjectId to search for.
    :type oid: str
    :param sectors: The list of sectors.
    :type sectors: list
    :param analyst: The user making the modifications.
    """

    obj = class_from_id(itype, oid)
    if not obj:
        return

    obj.add_sector_list(sectors, analyst, append=False)

    try:
        obj.save(username=analyst)
    except ValidationError:
        pass

def get_sector_options():
    """
    Get available sector options.

    :returns: list
    """

    sectors = SectorObject.objects()
    sector_list = [s.name for s in sectors]
    return HttpResponse(json.dumps(sector_list, default=json_handler),
                        content_type='application/json')

def get_bucket_autocomplete(term):
    """
    Get existing buckets to autocomplete.

    :param term: The current term to look for autocomplete options.
    :type term: str
    :returns: list
    """

    results = Bucket.objects(name__istartswith=term)
    buckets = [b.name for b in results]
    return HttpResponse(json.dumps(buckets, default=json_handler),
                        content_type='application/json')
