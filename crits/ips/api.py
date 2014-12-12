from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest
from mongoengine.base import ValidationError

from crits.ips.ip import IP
from crits.ips.handlers import ip_add_update
from crits.ips.handlers import ip_remove
from crits.campaigns.handlers import campaign_remove
from crits.core.handlers import source_remove_all
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource
from crits.core.user_tools import is_admin

import json

class IPResource(CRITsAPIResource):
    """
    Class to handle everything related to the IP API.

    Currently supports GET, POST, PATCH and DELETE.
    """

    class Meta:
        object_class = IP
        allowed_methods = ('get', 'post', 'delete', 'patch')
        resource_name = "ips"
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

        return super(IPResource, self).get_object_list(request, IP)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating IPs through the API.

        :param bundle: Bundle containing the information to create the IP.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        """

        analyst = bundle.request.user.username
        data = bundle.data
        ip = data.get('ip', None)
        name = data.get('source', None)
        reference = data.get('reference', None)
        method = data.get('method', None)
        campaign = data.get('campaign', None)
        confidence = data.get('confidence', None)
        ip_type = data.get('ip_type', None)
        add_indicator = data.get('add_indicator', False)
        indicator_reference = data.get('indicator_reference', None)
        bucket_list = data.get('bucket_list', None)
        ticket = data.get('ticket', None)

        content = {'return_code': 1,
                   'type': 'IP'}

        if not ip or not name or not ip_type:
            content['message'] = "Must provide an IP, IP Type, and Source."
            self.crits_response(content)

        result = ip_add_update(ip,
                               ip_type,
                               source=name,
                               source_method=method,
                               source_reference=reference,
                               campaign=campaign,
                               confidence=confidence,
                               analyst=analyst,
                               bucket_list=bucket_list,
                               ticket=ticket,
                               is_add_indicator=add_indicator,
                               indicator_reference=indicator_reference)

        if result.get('message'):
            content['message'] = result.get('message')
        if result.get('object'):
            content['id'] = str(result.get('object').id)
        if content.get('id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'ips',
                                  'api_name': 'v1',
                                  'pk': content.get('id')})
            content['url'] = url
        if result['success']:
            content['return_code'] = 0
        self.crits_response(content)


    def delete_detail(self, request, **kwargs):
        """
        This will delete a specific IP record. 

	The IP ID must be part of the URL (/api/v1/ips/{id}/)

        :param request: The incoming request.
        :type request: :class:`django.http.HttpRequest`
        :returns: HttpResponse.
        """
        content = {'return_code': 1,
                   'type': 'IP'}

        analyst = request.user.username

        if not is_admin(analyst):
          content['message'] = 'You must be an admin to delete IPs.'
          self.crits_response(content)

        path = request.path
        parts = path.split("/")
        id = parts[(len(parts) - 2)]

        if not id:
            content['message'] = "You must provide an IP ID."
            self.crits_response(content)

        try:
          result = ip_remove(id,analyst)
        except ValidationError,ve:
          content['message'] = "Could not locate IP ID."
          self.crits_response(content)

        if result.get('success'):
            content['return_code'] = 0

        self.crits_response(content)


    def patch_detail(self, request, **kwargs):
        """
        This will delete the campaign and source references within the IP
        ID's record. 

        The patch_detail method is for any modification to a record. The
        action parameter is hard coded to delete because that is the only
        modification that is currently supported.

        The data must be sent as JSON within the body of the request.

        This code assumes that the client has already deteremined whether there
        are multiple campaign/source associations.

        :param request: The incoming request.
        :type request: :class:`django.http.HttpRequest`
        :returns: HttpResponse.
        """
        content = {'return_code': 1,
                   'type': 'IP'}

        analyst = request.user.username
        data = json.loads(request.body)
        action = "delete"

        if not is_admin(analyst):
          content['message'] = 'You must be an admin to modify IPs.'
          self.crits_response(content)

        path = request.path
        parts = path.split("/")
        id = parts[(len(parts) - 2)]

        if not id:
            content['message'] = "You must provide an IP ID."
            self.crits_response(content)

        result = {}

        campaign = ""
        try:
          campaign = data.get("campaign")
        except KeyError, e:
          campaign = ""

        source = ""
        try:
          source = data.get("source")
        except KeyError, e:
          source = ""

        if ((source == None or source == "") and (campaign == None or campaign == "")):
            content['message'] = "A campaign or source must be provided."
            self.crits_response(content)

        if campaign != None and campaign != "":
          if action == "delete":
            result = campaign_remove("IP",id,campaign,analyst)

            if result == None:
              content['message'] = 'Could not remove campaign.'
              self.crits_response(content)

            if not result['success']:
              if result.get('message'):
                 content['message'] = result.get('message')
              else:
                 content['message'] = 'Could not remove campaign.'
              self.crits_response(content)

        if source != None and source != "":
          if action == "delete":
            result = source_remove_all("IP",id,source,analyst)

            if result == None:
              content['message'] = 'Could not remove source.'
              self.crits_response(content)

            if not result['success']:
              if result.get('message'):
                 content['message'] = result.get('message')
              else:
                 content['message'] = 'Could not remove source.'
              self.crits_response(content)

        if result.get('success'):
            content['return_code'] = 0

        self.crits_response(content)
