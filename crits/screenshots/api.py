from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource
from crits.screenshots.screenshot import Screenshot

class ScreenshotResource(CRITsAPIResource):
    """
    Class to handle everything related to the Screenshots API.

    Currently supports GET and POST.
    """

    class Meta:
        queryset = Screenshot.objects.all()
        allowed_methods = ('get', 'post')
        resource_name = "objects"
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
        raise BadRequest("Not working yet")
