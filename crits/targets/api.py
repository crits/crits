from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication

from crits.targets.target import Target
from crits.targets.handlers import upsert_target
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class TargetResource(CRITsAPIResource):
    """
    Class to handle everything related to the Target API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Target
        allowed_methods = ('get', 'post', 'patch')
        resource_name = "targets"
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

        return super(TargetResource, self).get_object_list(request, Target,
                                                           False)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating Targets through the API.

        :param bundle: Bundle containing the information to create the Target.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        """

        analyst = bundle.request.user.username
        data = bundle.data
        result = upsert_target(data, analyst)

        content = {'return_code': 0,
                   'type': 'Target',
                   'id': result.get('id', '')}
        if result.get('message'):
            content['message'] = result.get('message')
        if result.get('id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'targets',
                                  'api_name': 'v1',
                                  'pk': result.get('id')})
            content['url'] = url
            content['id'] = result.get('id')
        if not result['success']:
            content['return_code'] = 1
        self.crits_response(content)
