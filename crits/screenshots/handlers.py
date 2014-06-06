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
                   screenshot, screenshot_id, oid, otype):

    result = {'success': False}
    obj = class_from_id(otype, oid)
    if not obj:
        result['message'] = "Could not find the top-level object."
        return result

    if screenshot_id:
        screenshot_id = screenshot_id.strip().lower()
        s = Screenshot.objects(id=screenshot_id).first()
        if s:
            s.add_source(source=source, method=method, reference=reference,
                    analyst=analyst)
            s.save()
            obj.screenshots.append(screenshot_id)
            obj.save()
        else:
            result['message'] = "Could not find a screenshot with that ID."
            return result
    else:
        md5 = hashlib.md5(screenshot.read()).hexdigest()
        check = Screenshot.objects(md5=md5).first()
        if check:
            s = check
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
        except Exception, e:
            result['message'] = str(e)
            return result
        obj.screenshots.append(str(s.id))
        obj.save(username=analyst)

    result['message'] = "Screenshot successfully uploaded!"
    result['id'] = str(s.id)
    result['html'] = '<a href="%s" title="%s" data-id="%s" data-dialog><img src="%s"></a>' % \
        (reverse('crits.screenshots.views.render_screenshot',
                    args=[s.id]),
            s.description + ": " + ','.join(s.tags),
            str(s.id),
            reverse('crits.screenshots.views.render_screenshot',
                    args=[s.id, 'thumb']))
    result['success'] = True
    return result
