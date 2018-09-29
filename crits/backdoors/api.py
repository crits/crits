try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication

from crits.backdoors.backdoor import Backdoor
from crits.backdoors.handlers import add_new_backdoor
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource

from crits.vocabulary.acls import BackdoorACL

class BackdoorResource(CRITsAPIResource):
    """
    Class to handle everything related to the Backdoor API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Backdoor
        allowed_methods = ('get', 'post', 'patch')
        resource_name = "backdoors"
        ordering = ("name", "version", "description", "modified", "status",
                    "favorite", "id")
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

        user = bundle.request.user
        data = bundle.data
        name = data.get('name', None)
        version = data.get('version', '')
        aliases = data.get('aliases', '')
        description = data.get('description', None)
        source = data.get('source', None)
        reference = data.get('reference', None)
        method = data.get('method', None)
        tlp = data.get('tlp', 'amber')
        campaign = data.get('campaign', None)
        confidence = data.get('confidence', None)
        bucket_list = data.get('bucket_list', None)
        ticket = data.get('ticket', None)

        if user.has_access_to(BackdoorACL.WRITE):
            result = add_new_backdoor(name,
                                      version,
                                      aliases,
                                      description=description,
                                      source=source,
                                      source_method=method,
                                      source_reference=reference,
                                      source_tlp=tlp,
                                      campaign=campaign,
                                      confidence=confidence,
                                      user=user,
                                      bucket_list=bucket_list,
                                      ticket=ticket)

        else:
            result = {'success':False,
                      'message':'User does not have permission to create Object.'}

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
