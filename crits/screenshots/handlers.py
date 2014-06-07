import hashlib

from PIL import Image

from django.http import HttpResponse
from django.core.urlresolvers import reverse

from crits.core.class_mapper import class_from_id
from crits.screenshots.screenshot import Screenshot
from crits.core.user_tools import user_sources

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
    response = HttpResponse(mimetype="image/png")
    im.save(response, "PNG")
    return response

def add_screenshot(description, tags, source, method, reference, analyst,
                   screenshot, screenshot_ids, oid, otype):

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
        screenshot_list = screenshot_ids.split(',')
        for screenshot_id in screenshot_list:
            screenshot_id = screenshot_id.strip().lower()
            s = Screenshot.objects(id=screenshot_id).first()
            if s:
                s.add_source(source=source, method=method, reference=reference,
                        analyst=analyst)
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
            s.description = description
            s.md5 = md5
            screenshot.seek(0)
            s.add_screenshot(screenshot, tags)
        s.add_source(source=source, method=method, reference=reference,
                    analyst=analyst)
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
    if s.tags and s.description:
        description = s.description + ": " + ','.join(s.tags)
    else:
        description = s.md5
    html = '<a href="%s" title="%s" data-id="%s" data-dialog><img src="%s">' % \
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
