from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest
from bson.objectid import ObjectId

from crits.campaigns.campaign import Campaign
from crits.domains.domain import Domain
from crits.emails.email import Email
from crits.events.event import Event
from crits.indicators.indicator import Indicator
from crits.ips.ip import IP
from crits.pcaps.pcap import PCAP
from crits.samples.sample import Sample
from crits.raw_data.raw_data import RawData
from crits.actors.actor import Actor

from crits.campaigns.handlers import add_campaign, campaign_remove, remove_campaign
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource
from crits.core.class_mapper import class_from_type
from crits.core.user_tools import is_admin, user_sources



class CampaignResource(CRITsAPIResource):
    """
    Class to handle everything related to the Campaign API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Campaign
        allowed_methods = ('get', 'post','delete')
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

        """
        analyst = bundle.request.user.username
        name = bundle.data.get('name', None)
        description = bundle.data.get('description', None)
        aliases = bundle.data.get('aliases', None)
        bucket_list = bundle.data.get('bucket_list', None)
        ticket = bundle.data.get('ticket', None)

        content = {'return_code': 1,
                   'type': 'Campaign'}
        if not name:
            content['message'] = 'Need a Campaign name.'
            self.crits_response(content)

        result = add_campaign(name,
                              description,
                              aliases,
                              analyst,
                              bucket_list,
                              ticket)
        if result.get('id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'campaigns',
                                  'api_name': 'v1',
                                  'pk': result.get('id')})
            content['url'] = url
            content['id'] = result.get('id')

        if result['success']:
            content['return_code'] = 0

        content['message'] = result['message']
        self.crits_response(content)


    def delete_detail(self, request, **kwargs):
        """
        This will delete a specific campaign ID record.
        It will also delete all the campaign references in the TLOs.
        This will override the delete_detail in the core API.

        The campaign ID must be part of the URL (/api/v1/campaigns/{id}/)

        :param request: The incoming request.
        :type request: :class:`django.http.HttpRequest`
        :returns: HttpResponse.
        """
        content = {'return_code': 1,
                   'type': 'Campaign'}

        analyst = request.user.username
        if not is_admin(analyst):
          content['message'] = 'You must be an admin to delete campaigns.'
          self.crits_response(content)

        path = request.path
        parts = path.split("/")
        id = parts[(len(parts) - 2)]

        if not ObjectId.is_valid(id):
          content['message'] = 'You must provide a valid campaign ID.'
          self.crits_response(content)

        campaign = Campaign.objects(id=id).first()
        sources = user_sources(analyst)
 
        # Remove associations
        formatted_query = {'campaign.name': campaign.name}
        for obj_type in [Domain, PCAP, Indicator, Email, Sample, IP, Event, RawData, Actor]:
           
          objects = obj_type.objects(source__name__in=sources, __raw__=formatted_query)
          for obj in objects:
            result = campaign_remove(obj._meta['crits_type'],obj.id,campaign.name,analyst)

        result = remove_campaign(campaign.name, analyst)

        if result['success']:
          content['return_code'] = 0
        else:
          content['message'] = result['message']
        self.crits_response(content)
