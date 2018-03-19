import datetime
import json
import urllib

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string

from crits.comments.forms import AddCommentForm
from crits.comments.handlers import comment_add, comment_update, comment_remove
from crits.comments.handlers import get_aggregate_comments, get_activity
from crits.comments.handlers import generate_comment_jtable, generate_comment_csv
from crits.core.user_tools import user_can_view_data, get_acl_object
from crits.core.data_tools import json_handler
from crits.core.views import global_search_listing
from crits.vocabulary.acls import GeneralACL

@user_passes_test(user_can_view_data)
def comment_search(request):
    """
    Search for comments.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    query = {}
    query[request.GET.get('search_type', '')]=request.GET.get('q', '').strip()
    #return render(request, 'error.html', {'error': query})
    return HttpResponseRedirect(reverse('crits-comments-views-comments_listing')+
                                "?%s" % urllib.urlencode(query))


@user_passes_test(user_can_view_data)
def comments_listing(request,option=None):
    """
    Generate Comment Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_comment_csv(request)
    return generate_comment_jtable(request, option)

@user_passes_test(user_can_view_data)
def add_update_comment(request, method, obj_type, obj_id):
    """
    Add/update a comment for a top-level object. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param method: If this is a new comment or an update (set to "update").
    :type method: str
    :param obj_type: The type of the top-level object.
    :type obj_type: str
    :param obj_id: The ObjectId of the top-level object.
    :type obj_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        form = AddCommentForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            subscr = cleaned_data.get('subscribable', False)
            user = request.user
            acl = get_acl_object(obj_type)
            if method == "update":
                if user.has_access_to(acl.COMMENTS_EDIT):
                    return comment_update(cleaned_data, obj_type, obj_id,
                                          subscr, user.username)
                else:
                    result = {"success":False,
                              "message":"User does not have permission to edit comments."}
                    return HttpResponse(json.dumps(result),
                                        content_type="application/json")
            else:
                if user.has_access_to(acl.COMMENTS_ADD):
                    return comment_add(cleaned_data, obj_type, obj_id, method,
                                       subscr, user.username)
                else:
                    result = {"success":False,
                              "message":"User does not have permission to add comments."}
                    return HttpResponse(json.dumps(result),
                                        content_type="application/json")

        return HttpResponse(json.dumps({'success':False,
                                        'form':form.as_table()}),
                            content_type="application/json")
    return render(request, "error.html", {'error':'Expected AJAX/POST'})

@user_passes_test(user_can_view_data)
def remove_comment(request, obj_type, obj_id):
    """
    Remove a comment from a top-level object. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param obj_type: The TLO Type.
    :type obj_type: str
    :param obj_id: The ObjectId of the top-level object.
    :type obj_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        user = request.user
        date = datetime.datetime.strptime(request.POST['key'],
                                          settings.PY_DATETIME_FORMAT)
        acl = get_acl_object(obj_type)
        if user.has_access_to(acl.COMMENTS_DELETE):
            result = comment_remove(obj_id, user.username, date)
        else:
            result = {"success":False,
                      "message":"User does not have permission to remove comments."}
        return HttpResponse(json.dumps(result), content_type="application/json")
    return render(request, "error.html", {'error':'Expected AJAX/POST'})

@user_passes_test(user_can_view_data)
def get_new_comments(request):
    """
    Get new comments that aren't on the activity page. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        atype = 'all'
        value = None
        if 'atype' in request.POST:
            atype = request.POST['atype']
        if 'value' in request.POST:
            value = request.POST['value']
        if request.POST['convert'] == "true":
            date = datetime.datetime.fromtimestamp(int(request.POST['date'])/1000)
        else:
            date = datetime.datetime.strptime(request.POST['date'],
                                              settings.PY_DATETIME_FORMAT)
        if request.POST['convert'] =="false":
            delta = datetime.timedelta(microseconds=+1000)
            date = date + delta
        comments = get_aggregate_comments(atype,
                                          value,
                                          request.user.username,
                                          date)
        html = ''
        for comment in comments:
            username = {'username': '%s' % request.user.username}
            context = {'comment': comment, 'user': username}
            html += render_to_string('comments_row_widget.html', context, request=request)
        result = {'success': True, 'html': html}
        return HttpResponse(json.dumps(result,
                                       default=json_handler),
                            content_type="application/json")
    else:
        return render(request, "error.html", {'error':'Expected AJAX/POST'})

@user_passes_test(user_can_view_data)
def activity(request, atype=None, value=None):
    """
    Generate the Recent Activity page.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param atype: How to limit the results ("byuser", "bytag", "bycomment").
    :type atype: str
    :param value: If limiting by atype, what value should be used.
    :type value: str
    :returns: :class:`django.http.HttpResponse`
    """

    user = request.user
    analyst = user.username
    if not user.has_access_to(GeneralACL.RECENT_ACTIVITY_READ):
        return render(request, "error.html", {'error':'User does not have permission to view Recent Activity.'})
    if request.method == "POST" and request.is_ajax():
        atype = request.POST.get('atype', 'all')
        value = request.POST.get('value', None)
        date = request.POST.get('date', None)
        ajax = True
        return get_activity(atype,
                            value,
                            date,
                            analyst,
                            ajax)
    else:
        #site-wide advanced search passes as URL query string param
        if request.method == 'GET' and 'search' in request.GET:
            atype = request.GET.get('search_type')
            value = request.GET.get('q')
        date = request.POST.get('date', None)
        ajax = False

        if atype == 'byobject':
            return global_search_listing(request)
        (template, args) = get_activity(atype,
                                        value,
                                        date,
                                        analyst,
                                        ajax)
        return render(request, template, args, )
