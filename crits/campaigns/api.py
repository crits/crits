from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.campaigns.campaign import Campaign
from crits.campaigns.handlers import add_campaign
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class CampaignResource(CRITsAPIResource):
    """
    Class to handle everything related to the Campaign API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Campaign
        allowed_methods = ('get', 'post')
        resource_name = "campaigns"
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

        return super(CampaignResource, self).get_object_list(request, Campaign,
                                                             False)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating Campaigns through the API.

        :param bundle: Bundle containing the information to create the Campaign.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        :raises BadRequest: If a campaign name is not provided or creation fails.

        """
        analyst = bundle.request.user.username
        name = bundle.data.get('name', None)
        description = bundle.data.get('description', None)
        aliases = bundle.data.get('aliases', None)
        bucket_list = bundle.data.get('bucket_list', None)
        ticket = bundle.data.get('ticket', None)

        if not name:
            raise BadRequest('Need a Campaign name.')
        result =  add_campaign(name,
                                description,
                                aliases,
                                analyst,
                                bucket_list,
                                ticket)
        content = {'return_code': 0,
                   'type': 'Campaign',
                   'message': result.get('message', ''),
                   'id': result.get('id', '')}
        if result.get('id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'campaigns',
                                  'api_name': 'v1',
                                  'pk': result.get('id')})
            content['url'] = url
        if not result['success']:
            content['return_code'] = 1
        self.crits_response(content)
