import hashlib
import json

from PIL import Image

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse

from crits.core.class_mapper import class_from_id
from crits.core.crits_mongoengine import json_handler, create_embedded_source
from crits.core.crits_mongoengine import EmbeddedSource
from crits.core.handlers import build_jtable, jtable_ajax_list,jtable_ajax_delete
from crits.core.user_tools import user_sources
from crits.screenshots.screenshot import Screenshot

def get_screenshots_for_id(type_, _id, analyst, buckets=False):
    """
    Get screenshots for a top-level object.

    :param type_: The class type.
    :type type_: str
    :param _id: The ObjectId to lookup.
    :type _id: str
    :param analyst: The user looking up the screenshots.
    :type analyst: str
    :param buckets: Use buckets as tag lookups for screenshots.
    :type buckets: boolean
    :returns: list
    """

    result = {'success': False}
    sources = user_sources(analyst)

    obj = class_from_id(type_, _id)
    if not obj:
        result['message'] = "No valid top-level object found."
        return result
    screenshots = Screenshot.objects(id__in=obj.screenshots,
                                     source__name__in=sources)
    bucket_shots = Screenshot.objects(tags__in=obj.bucket_list,
                                      source__name__in=sources)

    final_shots = []
    for s in screenshots:
        if s.screenshot and s.thumb and s not in final_shots:
            final_shots.append(s)
    for b in bucket_shots:
        if b not in final_shots:
            # since .bucket isn't supported, this will show up in the template
            # under unsupported_attrs, which is ok.
            b.bucket = True
            final_shots.append(b)

    result['success'] = True
    result['screenshots'] = final_shots

    return result

def get_screenshot(_id=None, tag=None, analyst=None, thumb=False):
    """
    Get a screenshot.

    :param _id: The ObjectId to lookup.
    :type _id: str
    :param tag: The tag to look for.
    :type tag: str
    :param analyst: The user looking up the screenshots.
    :type analyst: str
    :returns: screenshot
    """

    if not analyst:
        return None
    sources = user_sources(analyst)

    if _id:
        screenshot = Screenshot.objects(id=_id,
                                        source__name__in=sources).first()
    if tag:
        screenshot = Screenshot.objects(tags=tag,
                                        source__name__in=sources).first()
    if not screenshot:
        return None

    if thumb:
        im = Image.open(screenshot.thumb)
    else:
        im = Image.open(screenshot.screenshot)
    response = HttpResponse(content_type="image/png")
    im.save(response, "PNG")
    return response

def add_screenshot(description, tags, source, method, reference, analyst,
                   screenshot, screenshot_ids, oid, otype):
    """
    Add a screenshot or screenshots to a top-level object.

    :param description: The description of the screenshot.
    :type description: str
    :param tags: Tags associated with this screenshot.
    :type tags: str, list
    :param source: The source who provided the screenshot.
    :type source_name: str,
                :class:`crits.core.crits_mongoengine.EmbeddedSource`,
                list of :class:`crits.core.crits_mongoengine.EmbeddedSource`
    :param method: The method of acquiring this screenshot.
    :type method: str
    :param reference: A reference to the source of this screenshot.
    :type reference: str
    :param analyst: The user adding the screenshot.
    :type analyst: str
    :param screenshot: The screenshot to add.
    :type screenshot: file handle
    :param screenshot_ids: A list of ObjectIds of existing screenshots to add.
    :type screenshot_ids: str, list
    :param oid: The ObjectId of the top-level object to add to.
    :type oid: str
    :param otype: The top-level object type.
    :type otype: str
    :returns: dict with keys:
              'success' (boolean),
              'message' (str),
              'id' (str) if successful,
              'html' (str) if successful,
    """

    result = {'success': False}
    if not source:
        result['message'] = "Must provide a source"
        return result
    obj = class_from_id(otype, oid)
    if not obj:
        result['message'] = "Could not find the top-level object."
        return result

    final_screenshots = []

    if screenshot_ids:
        if not isinstance(screenshot_ids, list):
            screenshot_list = screenshot_ids.split(',')
        else:
            screenshot_list = screenshot_ids
        for screenshot_id in screenshot_list:
            screenshot_id = screenshot_id.strip().lower()
            s = Screenshot.objects(id=screenshot_id).first()
            if s:
                if isinstance(source, basestring) and len(source) > 0:
                    s_embed = create_embedded_source(source, method=method,
                                                    reference=reference,
                                                    analyst=analyst)
                    s.add_source(s_embed)
                elif isinstance(source, EmbeddedSource):
                    s.add_source(source, method=method, reference=reference)
                elif isinstance(source, list) and len(source) > 0:
                    for x in source:
                        if isinstance(x, EmbeddedSource):
                            s.add_source(x, method=method, reference=reference)
                
                s.add_tags(tags)
                s.save()
                obj.screenshots.append(screenshot_id)
                obj.save()
                final_screenshots.append(s)
    else:
        md5 = hashlib.md5(screenshot.read()).hexdigest()
        check = Screenshot.objects(md5=md5).first()
        if check:
            s = check
            s.add_tags(tags)
        else:
            s = Screenshot()
            s.analyst = analyst
            s.description = description
            s.md5 = md5
            screenshot.seek(0)
            s.add_screenshot(screenshot, tags)
        if isinstance(source, basestring) and len(source) > 0:
            s_embed = create_embedded_source(source, method=method, reference=reference,
                                            analyst=analyst)
            s.add_source(s_embed)
        elif isinstance(source, EmbeddedSource):
            s.add_source(source, method=method, reference=reference)
        elif isinstance(source, list) and len(source) > 0:
            for x in source:
                if isinstance(x, EmbeddedSource):
                    s.add_source(x, method=method, reference=reference)
        
        if not s.screenshot and not s.thumb:
            result['message'] = "Problem adding screenshot to GridFS. No screenshot uploaded."
            return result
        try:
            s.save(username=analyst)
            final_screenshots.append(s)
        except Exception, e:
            result['message'] = str(e)
            return result
        obj.screenshots.append(str(s.id))
        obj.save(username=analyst)

    result['message'] = "Screenshot(s) successfully uploaded!"
    result['id'] = str(s.id)
    final_html = ""
    for f in final_screenshots:
        final_html += create_screenshot_html(f, oid, otype)
    result['html'] = final_html
    result['success'] = True
    return result

def create_screenshot_html(s, oid, otype):
    """
    Create HTML for a thumbnail view for the screenshot.

    :param s: The screenshot.
    :type s: :class:`crits.screenshots.screenshot.Screenshot`
    :param oid: The ObjectId of the top-level object it's associating with.
    :type oid: str
    :param otype: The type of top-level object it's associating with.
    :returns: str
    """

    if s.tags and s.description:
        description = s.description + ": " + ','.join(s.tags)
    else:
        description = s.md5
    description += " (submitted by %s)" % s.analyst
    html = '<a href="%s" title="%s" data-id="%s" data-dialog><img class="ss_no_bucket" src="%s">' % \
            (reverse('crits.screenshots.views.render_screenshot',
                    args=[s.id]),
            description,
            str(s.id),
            reverse('crits.screenshots.views.render_screenshot',
                    args=[s.id, 'thumb']))
    html += '<span class="remove_screenshot ui-icon ui-icon-trash" data-id="'
    html += '%s" data-obj="%s" data-type="%s" title="Remove from %s">' % (str(s.id),
                                                                          oid,
                                                                          otype,
                                                                          otype)
    html += '</span><span class="copy_ss_id ui-icon ui-icon-radio-on" '
    html += 'data-id="%s" title="Copy ID to clipboard"></span>' % str(s.id)

    return html

def delete_screenshot_from_object(obj, oid, sid, analyst):
    """
    Remove a screenshot from a top-level object.

    :param obj: The type of top-level object to work with.
    :type obj: str
    :param oid: The ObjectId of the top-level object to work with.
    :type oid: str
    :param sid: The ObjectId of the screenshot to remove.
    :type sid: str
    :param analyst: The user removing the screenshot.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str).
    """

    result = {'success': False}
    klass = class_from_id(obj, oid)
    if not klass:
        result['message'] = "Could not find Object to delete screenshot from."
        return result
    clean = [s for s in klass.screenshots if s != sid]
    klass.screenshots = clean
    try:
        klass.save(username=analyst)
        result['success'] = True
        return result
    except Exception, e:
        result['message'] = str(e)
        return result

def generate_screenshot_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = Screenshot
    type_ = "screenshot"
    mapper = obj_type._meta['jtable_opts']
    if option == "jtlist":
        # Sets display url
        details_url = mapper['details_url']
        details_url_key = mapper['details_url_key']
        fields = mapper['fields']
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
        'title': "Screenshots",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits.%ss.views.%ss_listing' % (type_,
                                                            type_),
                           args=('jtlist',)),
        'deleteurl': reverse('crits.%ss.views.%ss_listing' % (type_,
                                                              type_),
                             args=('jtdelete',)),
        'searchurl': reverse(mapper['searchurl']),
        'fields': mapper['jtopts_fields'],
        'hidden_fields': mapper['hidden_fields'],
        'linked_fields': mapper['linked_fields'],
        'details_link': mapper['details_link'],
        'no_sort': mapper['no_sort']
    }
    jtable = build_jtable(jtopts,request)
    jtable['toolbar'] = []
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
