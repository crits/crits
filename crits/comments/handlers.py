import datetime
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
try:
    from mongoengine.base import ValidationError
except ImportError:
    from mongoengine.errors import ValidationError

from crits.comments.comment import Comment
from crits.comments.forms import JumpToDateForm
from crits.core.class_mapper import class_from_type
from crits.core.crits_mongoengine import create_embedded_source, json_handler
from crits.core.handlers import jtable_ajax_list,build_jtable, jtable_ajax_delete
from crits.core.handlers import csv_export
from crits.core.user_tools import get_user_organization, user_sources

def generate_comment_csv(request):
    """
    Generate a CSV file of the Comments.

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request,Comment)
    return response

def get_comments(obj_id, obj_type):
    """
    Get Comments for a specific top-level object.

    :param obj_id: The ObjectId to search for.
    :type obj_id: str
    :param obj_type: The top-level object type.
    :type obj_type: str
    :returns: list of :class:`crits.comments.comment.Comment`
    """

    #TODO: add source filtering for non-UI based applications
    results = Comment.objects(obj_id=obj_id,
                              obj_type=obj_type).order_by('+created')
    final_comments = []
    for result in results:
        result.comment_to_html()
        final_comments.append(result)
    return final_comments

def get_aggregate_comments(atype, value, username, date=None):
    """
    Generate a list of comments for the aggregate view.

    :param atype: How to limit the comments ("bytag", "byuser", "bycomment").
    :type atype: str
    :param value: If limiting by atype, the value to limit by.
    :type value: str
    :param username: The user getting the comments.
    :type username: str
    :param date: The specific date to get comments for.
    :type date: datetime.datetime
    :returns: list of :class:`crits.comments.comment.Comment`
    """

    results = None
    if date:
        end_date = date+datetime.timedelta(days=1)
        query = {'date':{'$gte':date, '$lte':end_date}}
    else:
        query = {}
    if atype == 'bytag':
        query['tags'] = value
    elif atype == 'byuser':
        query['$or'] = [{'users':value}, {'analyst':value}]
    elif atype == 'bycomment':
        query['comment'] = {'$regex':value}

    results = Comment.objects(__raw__=query)
    sources = user_sources(username)
    return get_user_allowed_comments(results, sources)

def get_user_allowed_comments(comments, sources):
    """
    Limit the comments to those a user should have access to see.

    :param comments: The list of comments.
    :type comments: list
    :param sources: The sources the user has access to.
    :type sources: list
    :returns: list of :class:`crits.comments.comment.Comment`
    """

    docs = {'Actor': {},
            'Campaign':{},
            'Certificate':{},
            'Domain':{},
            'Email':{},
            'Event':{},
            'Indicator':{},
            'IP':{},
            'PCAP':{},
            'RawData':{},
            'Sample':{},
            'Target':{}}
    for c in comments:
        c.comment_to_html()
        try:
            docs[c.obj_type][c.obj_id].append(c)
        except KeyError:
            docs[c.obj_type][c.obj_id] = [c]

    final_comments = []
    for key, val in docs.items():
        cls = class_from_type(key)
        obj_ids = [v for v in val] #get keys
        query = {'_id': {'$in':obj_ids},
                 '$or': [{'source.name': {'$in':sources}},
                         {'source': {'$exists': 0}}
                         ]
                 }
        result = cls.objects(__raw__=query).only('id')
        for r in result:
            final_comments += val[r.id]
    final_comments.sort(key=lambda x: x.created, reverse=True)
    return final_comments

def generate_comment_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = Comment
    type_ = "comment"
    if option == "jtlist":
        # Sets display url
        details_url = ''
        details_url_key = "id"
        fields = ["obj_type", "comment", "url_key", "created",
                   "analyst", "source", "id"]
        response = jtable_ajax_list(obj_type,
                                    details_url,
                                    details_url_key,
                                    request,
                                    includes=fields)
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    if option == "jtdelete":
        response = {"Result": "ERROR"}
        if jtable_ajax_delete(obj_type,request):
            response = {"Result": "OK"}
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    jtopts = {
        'title': "Comments",
        'default_sort': "date DESC",
        'listurl': reverse('crits.%ss.views.%ss_listing' % (type_,
                                                            type_),
                           args=('jtlist',)),
        'deleteurl': reverse('crits.%ss.views.%ss_listing' % (type_,
                                                              type_),
                             args=('jtdelete',)),
        'searchurl': reverse('crits.%ss.views.%ss_listing' % (type_,type_)),
        'fields': ["details",
                   "obj_type",
                   "comment",
                   "date",
                   "analyst",
                   "source",
                   "id"],
        'hidden_fields': ["id", ],
        'linked_fields': ["analyst", ],
        'details_link': 'details',
        'no_sort': ['details', ],
    }
    jtable = build_jtable(jtopts,request)
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

def comment_add(cleaned_data, obj_type, obj_id, method, subscr, analyst):
    """
    Add a new comment.

    :param cleaned_data: Cleaned data from the Django form submission.
    :type cleaned_data: dict
    :param obj_type: The top-level object type to add the comment to.
    :type obj_type: str
    :param obj_id: The top-level ObjectId to add the comment to.
    :type obj_id: str
    :param method: If this is a reply or not (set method to "reply").
    :type method: str
    :param subscr: The subscription information for the top-level object.
    :type subscr: dict
    :param analyst: The user adding the comment.
    :type analyst: str
    :returns: dict with keys:
              'success' (boolean),
              'message': (str),
              'html' (str) if successful.
    """

    comment = Comment()
    comment.comment = cleaned_data['comment']
    comment.parse_comment()
    comment.set_parent_object(obj_type, obj_id)
    if method == "reply":
        comment.set_parent_comment(cleaned_data['parent_date'],
                                   cleaned_data['parent_analyst'])
    comment.analyst = analyst
    comment.set_url_key(cleaned_data['url_key'])
    source = create_embedded_source(name=get_user_organization(analyst),
                                    analyst=analyst)
    comment.source = [source]
    try:
        comment.save(username=analyst)
        # this is silly :( in the comment object the dates are still
        # accurate to .###### seconds, but in the database are only
        # accurate to .### seconds. This messes with the template's ability
        # to compare creation and edit times.
        comment.reload()
        comment.comment_to_html()
        html = render_to_string('comments_row_widget.html',
                                {'comment': comment,
                                 'user': {'username': analyst},
                                 'subscription': subscr})
        message = "Comment added successfully!"
        result = {'success': True, 'html': html, 'message': message}
    except ValidationError, e:
        result = {'success': False, 'message': e}
    return HttpResponse(json.dumps(result,
                        default=json_handler),
                        content_type="application/json")

def comment_update(cleaned_data, obj_type, obj_id, subscr, analyst):
    """
    Update an existing comment.

    :param cleaned_data: Cleaned data from the Django form submission.
    :type cleaned_data: dict
    :param obj_type: The top-level object type to find the comment to update.
    :type obj_type: str
    :param obj_id: The top-level ObjectId to find the comment to update.
    :type obj_id: str
    :param subscr: The subscription information for the top-level object.
    :type subscr: dict
    :param analyst: The user updating the comment.
    :type analyst: str
    :returns: :class:`django.http.HttpResponse`
    """

    result = None
    date = cleaned_data['parent_date']
    comment = Comment.objects(obj_id=obj_id,
                              created=date).first()
    if not comment:
        message = "Cannot find comment to update!"
        result = {'success': False, 'message': message}
    elif comment.analyst != analyst:
        # Should admin users be able to edit others comments?
        message = "You cannot edit comments from other analysts!"
        result = {'success': False, 'message': message}
    else:
        comment.edit_comment(cleaned_data['comment'])
        try:
            comment.save()
            comment.comment_to_html()
            html = render_to_string('comments_row_widget.html',
                                    {'comment': comment,
                                     'user': {'username': analyst},
                                     'subscription': subscr})
            message = "Comment updated successfully!"
            result = {'success': True, 'html': html, 'message': message}
        except ValidationError, e:
            result = {'success': False, 'message': e}
    return HttpResponse(json.dumps(result,
                                   default=json_handler),
                        content_type="application/json")

def comment_remove(obj_id, analyst, date):
    """
    Remove an existing comment.

    :param obj_id: The top-level ObjectId to find the comment to remove.
    :type obj_id: str
    :param analyst: The user removing the comment.
    :type analyst: str
    :param date: The date of the comment to remove.
    :type date: datetime.datetime
    :returns: dict with keys "success" (boolean) and "message" (str).
    """

    comment = Comment.objects(obj_id=obj_id,
                              created=date).first()
    if not comment:
        message = "Could not find comment to remove!"
        result = {'success': False, 'message': message}
    elif comment.analyst != analyst:
        # Should admin users be able to delete others comments?
        message = "You cannot delete comments from other analysts!"
        result = {'success': False, 'message': message}
    else:
        comment.delete()
        message = "Comment removed successfully!"
        result = {'success': True, 'message': message}
    return result

def get_activity(atype, value, date, analyst, ajax):
    """
    Generate comment activity for the Recent Activity page.

    :param atype: How to limit the comments ("bytag", "byuser", "bycomment").
    :type atype: str
    :param value: If limiting by atype, the value to limit by.
    :type value: str
    :param date: The specific date to get comments for.
    :type date: datetime.datetime
    :param analyst: The user getting the comments.
    :type analyst: str
    :param ajax: Whether or not this is an AJAX request.
    :type ajax: boolean
    :returns: :class:`django.http.HttpResponse` if AJAX.
              dict with template and arguments if not.
    """

    if date:
        date = datetime.datetime.strptime(date, settings.PY_DATE_FORMAT)
    else:
        date = datetime.datetime.today().replace(hour=0,
                                                    minute=0,
                                                    second=0,
                                                    microsecond=0)
    delta = datetime.timedelta(days=1)

    if ajax:
        yesterday = date - delta
        tomorrow = date + delta
        comments = get_aggregate_comments(atype,
                                          value,
                                          analyst,
                                          date)
        context = {'aggregate': True,
                   'today': date,
                   'yesterday': yesterday,
                   'tomorrow': tomorrow,
                   'comments': {'comments': comments}}
        result = {'success': True}
        result['html'] = render_to_string('comments_listing_widget.html',
                                          context)
        return HttpResponse(json.dumps(result,
                                       default=json_handler),
                            content_type="application/json")
    else:
        #TODO: bysubscription ?
        if atype not in ('byuser', 'bytag', 'bycomment'):
            atype = 'all'
        comments = get_aggregate_comments(atype,
                                          value,
                                          analyst,
                                          date)

        if len(comments):
            oldest = comments[-1]['created']
            newest = comments[0]['created']
            yesterday = oldest - delta
            tomorrow = newest + delta
        else:
            yesterday = date - delta
            tomorrow = date + delta

        date_form = JumpToDateForm()
        template = "comments_aggregate.html"
        args = {'comments': {'comments': comments},
                'type': atype,
                'jump_to_date_form': date_form,
                'yesterday': yesterday,
                'today': date,
                'tomorrow': tomorrow,
                'atype':atype,
                'value':value}

        return template, args
