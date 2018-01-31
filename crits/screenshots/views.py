import json

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import render

from crits.core.user_tools import user_can_view_data, get_acl_object
from crits.screenshots.handlers import get_screenshots_for_id, get_screenshot
from crits.screenshots.handlers import add_screenshot, generate_screenshot_jtable
from crits.screenshots.handlers import delete_screenshot_from_object

from crits.vocabulary.acls import ScreenshotACL


@user_passes_test(user_can_view_data)
def screenshots_listing(request,option=None):
    """
    Generate Screenshots Listing template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param option: Whether or not we should generate a CSV (yes if option is "csv")
    :type option: str
    :returns: :class:`django.http.HttpResponse`
    """

    return generate_screenshot_jtable(request, option)

@user_passes_test(user_can_view_data)
def get_screenshots(request):
    """
    Get screenshots for a top-level object. Should be an AJAX POST.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        analyst = request.user.username
        type_ = request.POST.get('type', None)
        _id = request.POST.get('id', None)
        buckets = request.POST.get('buckets', False)
        result = get_screenshots_for_id(type_, _id, analyst, buckets)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def find_screenshot(request):
    """
    Find a screenshot by tag or ObjectId.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    analyst = request.user.username
    if request.method == 'POST':
        _id = request.POST.get('id', None)
        tag = request.POST.get('tag', None)
    if request.method == 'GET':
        _id = request.GET.get('id', None)
        tag = request.GET.get('tag', None)
        result = get_screenshot(_id, tag, analyst)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Could not get screenshot."
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def render_screenshot(request, _id, thumb=None):
    """
    Get a screenshot by ObjectId.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    analyst = request.user.username
    result = get_screenshot(_id=_id, analyst=analyst, thumb=thumb)
    if not result:
        return HttpResponse(json.dumps(''),
                            content_type="application/json")
    else:
        return result

@user_passes_test(user_can_view_data)
def add_new_screenshot(request):
    """
    Add a new screenshot.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    user = request.user
    description = request.POST.get('description', None)
    reference = request.POST.get('source_reference', None)
    method = request.POST.get('source_method', None)
    tlp = request.POST.get('source_tlp', None)
    tags = request.POST.get('tags', None)
    source = request.POST.get('source_name', None)
    oid = request.POST.get('oid', None)
    otype = request.POST.get('otype', None)
    screenshot_ids = request.POST.get('screenshot_ids', None)
    screenshot = request.FILES.get('screenshot', None)

    acl = get_acl_object(otype)

    if user.has_access_to(acl.SCREENSHOTS_ADD):
        result = add_screenshot(description, tags, source, method, reference, tlp,
                                user.username, screenshot, screenshot_ids, oid, otype)
    else:
        result = {"success":False,
                  "message":"User does not have permission to add screenshots."}

    return HttpResponse(json.dumps(result),
                        content_type="application/json")

@user_passes_test(user_can_view_data)
def remove_screenshot_from_object(request):
    """
    Removes the screenshot from being associated with a top-level object.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    user = request.user
    obj = request.POST.get('obj', None)
    oid = request.POST.get('oid', None)
    sid = request.POST.get('sid', None)

    if user.has_access_to(str(obj + ScreenshotACL.SCREENSHOT_DELETE )):
        result = delete_screenshot_from_object(obj, oid, sid, user)
    else:
        result = {"success":False,
                  "message":"User does not have permission to remove screenshots."}
    return HttpResponse(json.dumps(result),
                        content_type="application/json")
