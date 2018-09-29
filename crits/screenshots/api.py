try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource
from crits.core.user_tools import get_acl_object
from crits.screenshots.handlers import add_screenshot
from crits.screenshots.screenshot import Screenshot

class ScreenshotResource(CRITsAPIResource):
    """
    Class to handle everything related to the Screenshots API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Screenshot
        allowed_methods = ('get', 'post')
        resource_name = "screenshots"
        ordering = ("thumb", "description", "created", "id", "md5", "tags")
        authentication = MultiAuthentication(CRITsApiKeyAuthentication(),
                                             CRITsSessionAuthentication())
        authorization = authorization.Authorization()
        serializer = CRITsSerializer()

    def get_object_list(self, request):
        """
        Use the CRITsAPIResource to get our objects but provide the class to get
        the objects from.

        :param request: The incoming request.
        :type request: :class:`django.http.HttpRequest`
        :returns: Resulting objects in the specified format (JSON by default).
        """

        return super(ScreenshotResource, self).get_object_list(request,
                                                               Screenshot,
                                                               False)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating Screenshots through the API.

        :param bundle: Bundle containing the information to create the
                       Screenshot.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        """

        user = bundle.request.user
        type_ = bundle.data.get('upload_type', None)

        content = {'return_code': 1,
                   'type': 'Screenshot'}

        if not type_:
            content['message'] = 'Must provide an upload type.'
            self.crits_response(content)
        if type_ not in ('ids', 'screenshot'):
            content['message'] = 'Not a valid upload type.'
            self.crits_response(content)
        if type_ == 'ids':
            screenshot_ids = bundle.data.get('screenshot_ids', None)
            screenshot = None
        elif type_ == 'screenshot':
            screenshot = bundle.data.get('filedata', None)
            screenshot_ids = None
            if not screenshot:
                content['message'] = "Upload type of 'screenshot' but no file uploaded."
                self.crits_response(content)

        description = bundle.data.get('description', None)
        tags = bundle.data.get('tags', None)
        source = bundle.data.get('source', None)
        method = bundle.data.get('method', None)
        reference = bundle.data.get('reference', None)
        tlp = bundle.data.get('tlp', 'amber')
        oid = bundle.data.get('oid', None)
        otype = bundle.data.get('otype', None)


        if not oid or not otype or not source or not (screenshot or screenshot_ids):
            content['message'] = "You must provide a valid set of information."
            self.crits_response(content)

        acl = get_acl_object(otype)
        if not user.has_access_to(acl.SCREENSHOTS_ADD):
            content['message'] = 'User does not have permission to create Object.'
            self.crits_response(content)

        result = add_screenshot(description, tags, source, method, reference,
                                tlp, user.username, screenshot, screenshot_ids, oid, otype)

        if result.get('message'):
            content['message'] = result.get('message')

        if result.get('id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'screenshots',
                                  'api_name': 'v1',
                                  'pk': result.get('id')})
            content['url'] = url
            content['id'] = result.get('id')

        if result['success']:
            content['return_code'] = 0
        self.crits_response(content)
