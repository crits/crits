from tastypie import authorization
from tastypie.authentication import MultiAuthentication

from crits.sources.source import Source
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource
from crits.core.handlers import get_source_names


class SourceResource(CRITsAPIResource):
    """
    Class to handle everything related to the Event API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Source
        allowed_methods = ('get')
        resource_name = "sources"
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
        username = request.user.username
        choices = [c.name for c in get_source_names(True, True, username)]
        resp = {'return_code': 0, 'type': 'Source', 'sources': choices}
        return super(SourceResource, self).crits_response(resp)
