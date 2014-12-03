from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.ips.ip import IP
from crits.ips.handlers import ip_add_update
from crits.ips.handlers import ip_remove
from crits.campaigns.handlers import campaign_remove
from crits.core.handlers import source_remove_all
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class IPResource(CRITsAPIResource):
    """
    Class to handle everything related to the IP API.

    Currently supports GET, POST, and DELETE.
    """

    class Meta:
        object_class = IP
        allowed_methods = ('get', 'post', 'delete')
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


    def obj_delete_list(self, bundle, **kwargs):
        """
        Handles deleting an IP associated with an IP ID from CRITs.
        Variables must be sent in the URL and not as a POST body.

        If a campaign or source is provided with the IP ID, then this will just delete those references form the IP record.
        If the request provides only an IP ID, then this will delete the entire record.
        This assumes that the client has deteremined whether there are multiple campaign/source associations or not.

        :param bundle: Bundle containing the information to delete the IP.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        """
        analyst = bundle.request.user.username

        ip_id = bundle.request.REQUEST["ip_id"]

        content = {'return_code': 1,
                   'type': 'IP'}

        if not ip_id:
            content['message'] = "You must provide an IP ID."
            self.crits_response(content)

        result = {}

        campaign = ""
        try:
          campaign = bundle.request.REQUEST.get("campaign")
        except KeyError, e:
          campaign = ""

        source = ""
        try:
          source = bundle.request.REQUEST.get("source")
        except KeyError, e:
          source = ""

        if campaign != None and campaign != "":
            result = campaign_remove("IP",ip_id,campaign,analyst)
            if not result['success']:
              if result.get('message'):
                 content['message'] = result.get('message')
              self.crits_response(content)

        if source != None and source != "":
            result = source_remove_all("IP",ip_id,source,analyst)
            if not result['success']:
              if result.get('message'):
                 content['message'] = result.get('message')
              self.crits_response(content)

        if ((source == None or source == "") and (campaign == None or campaign == "")):
            result = ip_remove(ip_id,analyst)

        if result.get('message'):
            content['message'] = result.get('message') + " " + campaign + " " + source

        if result.get('success'):
            content['return_code'] = 0

        self.crits_response(content)
