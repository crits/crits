from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource
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
        :returns: Bundle object.
        :raises BadRequest: If filedata is not provided or creation fails.
        """

        analyst = bundle.request.user.username
        type_ = bundle.data.get('upload_type', None)
        if not type_:
            raise BadRequest('Must provide an upload type.')
        if type_ not in ('ids', 'screenshot'):
            raise BadRequest('Not a valid upload type.')
        if type_ == 'ids':
            screenshot_ids = bundle.data.get('screenshot_ids', None)
            screenshot = None
        elif type_ == 'screenshot':
            screenshot = bundle.data.get('filedata', None)
            screenshot_ids = None
            if not screenshot:
                raise BadRequest("Upload type of 'screenshot' but no file uploaded.")

        description = bundle.data.get('description', None)
        tags = bundle.data.get('tags', None)
        source = bundle.data.get('source', None)
        method = bundle.data.get('method', None)
        reference = bundle.data.get('reference', None)
        oid = bundle.data.get('oid', None)
        otype = bundle.data.get('otype', None)

        if not oid and not otype and not source and not (screenshot or screenshot_ids):
            raise BadRequest("You must provide a valid set of information.")

        result = add_screenshot(description, tags, source, method, reference,
                                analyst, screenshot, screenshot_ids, oid, otype)

        if result['success']:
            return bundle
        else:
            err = result['message']
            raise BadRequest('Unable to create screenshot from data. %s' % err)
