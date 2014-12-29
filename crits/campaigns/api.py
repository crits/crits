from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.campaigns.campaign import Campaign
from crits.campaigns.handlers import add_campaign, campaign_remove, remove_campaign
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource
from crits.core.class_mapper import class_from_type
from crits.core.mongo_tools import validate_objectid
from crits.core.user_tools import is_admin, user_sources


import json


class CampaignResource(CRITsAPIResource):
    """
    Class to handle everything related to the Campaign API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Campaign
        allowed_methods = ('get', 'post','patch','delete')
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

        result =  add_campaign(name,
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


    def patch_detail(self, request, **kwargs):
        """
        This will delete domain/ip references within the campaign ID's record.

        The patch_detail method is for any modification to a record. The
        action parameter is hard coded to delete because that is the only
        modification that is currently supported.

        The data must be sent as JSON within the body of the request.
	The crits_type will specify what will be removed ("IP","Domain").
        The crits_id is the ID of the obj_type that will be removed.

        :param request: The incoming request.
        :type request: :class:`django.http.HttpRequest`
        :returns: HttpResponse.
        """

        content = {'return_code': 1,
                   'type': 'Campaign'}

        analyst = request.user.username
        data = json.loads(request.body)
        action = "delete"

        if not is_admin(analyst):
          content['message'] = 'You must be an admin to modify campaigns.'
          self.crits_response(content)

        path = request.path
        parts = path.split("/")
        id = parts[(len(parts) - 2)]
 
        if not validate_objectid(id):
          content['message'] = 'You must provide a valid campaign ID.'
          self.crits_response(content)

        obj_type = ""
        try:
          obj_type = data.get("crits_type")
        except KeyError, e:
          content['message'] = 'A crits_type must be provided.'
          self.crits_response(content)

        obj_id = ""
        try:
          obj_id = data.get("crits_id")
        except KeyError, e:
          content['message'] = 'A crits_id must be provided.'
          self.crits_response(content)

        if not validate_objectid(obj_id):
          content['message'] = 'Invalid crits_id.'
          self.crits_response(content)

        obj = class_from_type(obj_type)
        if obj == None:
          content['message'] = 'Invalid crits_type'
          self.crits_response(content)

        sources = user_sources(analyst)
        doc = obj.objects(id=obj_id,source__name__in=sources).first()

        if not doc:
          content['message'] = 'The provided ID is not available to the provided account.'
          self.crits_response(content)

        campaign = Campaign.objects(id=id).first()

        result = campaign_remove(obj_type,obj_id,campaign.name,analyst)

        if result == None:
           content['message'] = 'Could not remove the campaign.'
           self.crits_response(content)

        if not result['success']:
           if result.get('message'):
              content['message'] = result.get('message')
           else:
              content['message'] = 'Could not remove the campaign.'
        else:
           content['return_code'] = 0

        self.crits_response(content)


    def delete_detail(self, request, **kwargs):
        """
        This will delete a specific campaign ID record.

        The campaign ID must be part of the URL (/api/v1/campaigns/{id}/)

        :param request: The incoming request.
        :type request: :class:`django.http.HttpRequest`
        :returns: HttpResponse.
        """
        content = {'return_code': 1,
                   'type': 'Campaign'}

        username = request.user.username
        if not is_admin(username):
          content['message'] = 'You must be an admin to delete campaigns.'
          self.crits_response(content)

        path = request.path
        parts = path.split("/")
        id = parts[(len(parts) - 2)]

        if not validate_objectid(id):
          content['message'] = 'You must provide a valid campaign ID.'
          self.crits_response(content)

        campaign = Campaign.objects(id=id).first()
        result = remove_campaign(campaign.name, username)

        if result['success']:
          content['return_code'] = 0
        else:
          content['message'] = result['message']
        self.crits_response(content)
