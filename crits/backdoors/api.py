from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication

from crits.backdoors.backdoor import Backdoor
from crits.backdoors.handlers import add_new_backdoor
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class BackdoorResource(CRITsAPIResource):
    """
    Class to handle everything related to the Backdoor API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Backdoor
        allowed_methods = ('get', 'post', 'patch')
        resource_name = "backdoors"
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

        return super(BackdoorResource, self).get_object_list(request, Backdoor)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating Backdoors through the API.

        :param bundle: Bundle containing the information to create the Backdoor.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse object.
        """

        user = bundle.request.user.username
        data = bundle.data
        name = data.get('name', None)
        version = data.get('version', '')
        aliases = data.get('aliases', '')
        description = data.get('description', None)
        source = data.get('source', None)
        reference = data.get('reference', None)
        method = data.get('method', None)
        campaign = data.get('campaign', None)
        confidence = data.get('confidence', None)
        bucket_list = data.get('bucket_list', None)
        ticket = data.get('ticket', None)

        result = add_new_backdoor(name,
                                  version,
                                  aliases,
                                  description=description,
                                  source=source,
                                  source_method=method,
                                  source_reference=reference,
                                  campaign=campaign,
                                  confidence=confidence,
                                  user=user,
                                  bucket_list=bucket_list,
                                  ticket=ticket)

        content = {'return_code': 0,
                   'type': 'Backdoor',
                   'message': result.get('message', ''),
                   'id': result.get('id', '')}
        if result.get('id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'backdoors',
                                  'api_name': 'v1',
                                  'pk': result.get('id')})
            content['url'] = url
        if not result['success']:
            content['return_code'] = 1
        self.crits_response(content)
