from dateutil.parser import parse
from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.domains.domain import Domain
from crits.domains.handlers import add_new_domain, add_whois, generate_domain_jtable

from crits.campaigns.handlers import campaign_remove
from crits.core.handlers import source_remove_all
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class temp_request(object):
    """
    This is an empty class for creating a fake POST request in obj_delete_list
    """
    pass


class DomainResource(CRITsAPIResource):
    """
    Domain API Resource Class.
    """

    class Meta:
        object_class = Domain
        allowed_methods = ('get', 'post', 'delete')
        resource_name = "domains"
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

        return super(DomainResource, self).get_object_list(request, Domain)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating Domains through the API.

        :param bundle: Bundle containing the information to create the Domain.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        """

        request = bundle.request
        # Domain and source information
        domain = bundle.data.get('domain', None)
        name = bundle.data.get('source', None)
        reference = bundle.data.get('reference', None)
        method = bundle.data.get('method', None)
        # Campaign information
        campaign = bundle.data.get('campaign', None)
        confidence = bundle.data.get('confidence', None)
        # Also add IP information
        add_ip = bundle.data.get('add_ip', None)
        ip = bundle.data.get('ip', None)
        same_source = bundle.data.get('same_source', None)
        ip_source = bundle.data.get('ip_source', None)
        ip_method = bundle.data.get('ip_method', None)
        ip_reference = bundle.data.get('ip_reference', None)
        # Also add indicators
        add_indicators = bundle.data.get('add_indicators', None)
        bucket_list = bundle.data.get('bucket_list', None)
        ticket = bundle.data.get('ticket', None)

        data = {'domain_reference': reference,
                'domain_source': name,
                'domain_method': method,
                'confidence': confidence,
                'campaign': campaign,
                'domain': domain,
                'same_source': same_source,
                'ip_source': ip_source,
                'ip_method': ip_method,
                'ip_reference': ip_reference,
                'add_ip': add_ip,
                'ip': ip,
                'add_indicators': add_indicators,
                'bucket_list': bucket_list,
                'ticket': ticket}

        content = {'return_code': 1,
                   'type': 'Domain'}
        if not domain:
            content['message'] = 'Need a Domain Name.'
            self.crits_response(content)

        # The empty list is necessary. The function requires a list of
        # non-fatal errors so it can be added to if any other errors
        # occur. Since we have none, we pass the empty list.
        (result, errors, retVal) =  add_new_domain(data,
                                                   request,
                                                   [])
        if not 'message' in retVal:
            retVal['message'] = ""
        elif not isinstance(retVal['message'], basestring):
            retVal['message'] = str(retVal['message'])
        if errors:
            for e in errors:
                retVal['message'] += " %s " % str(e)

        obj = retVal.get('object', None)
        content['message'] = retVal.get('message', '')
        if obj:
            content['id'] = str(obj.id)
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'domains',
                                  'api_name': 'v1',
                                  'pk': str(obj.id)})
            content['url'] = url

        if result:
            content['return_code'] = 0

        self.crits_response(content)


    def obj_delete_list(self, bundle, **kwargs):
        """
        This will delete a specific domain ID.
        Variables must be sent in the URL and not as a POST body.

        If a campaign or source is provided with the domain ID, then this will just delete those references from the domain record.
        If the request contains only the domain ID, then the entire record will be deleted.
        This assumes that the client has deteremined whether there are multiple campaign/source associations or not.


        :param bundle: Bundle containing the information to create the Domain.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        """

        analyst = bundle.request.user.username
        id = bundle.request.REQUEST["id"]

        if not id:
          content['message'] = 'You must provide a domain ID.'
          self.crits_response(content)

        content = {'return_code': 1,
                   'type': 'Domain'}

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
            result = campaign_remove("Domain",id,campaign,analyst)
            if not result['success']:
              if result.get('message'):
                 content['message'] = result.get('message')
              self.crits_response(content)

        if source != None and source != "":
            result = source_remove_all("Domain",id,source,analyst)
            if not result['success']:
              if result.get('message'):
                 content['message'] = result.get('message')
              self.crits_response(content)

        if ((source == None or source == "") and (campaign == None or campaign == "")):
          """
          Mongo Engine won't accept a DELETE request with a POST request body.
          Therefore, DELETE requests must send the variables in the URL similar to GET requests.
          However, the jtable code expects a POST request format.
          This code will covert the GET format of a DELETE request to a POST format using temp_request so that it will be accepted by the jtable code.
          """

          fake_request = temp_request()
          fake_request.user = temp_request()
          fake_request.user.username = analyst
          fake_request.POST = {}
          fake_request.POST['id'] = id

          jtable_result = generate_domain_jtable(fake_request,"jtdelete")
          content['message'] = jtable_result.content

          if 'OK' in content['message']:
            content['return_code'] = 0

        if result.get('message'):
            content['message'] = result.get('message') + " " + campaign + " " + source

        if result.get('success'):
            content['return_code'] = 0

        self.crits_response(content)


class WhoIsResource(CRITsAPIResource):
    """
    Domain Whois API Resource Class.
    """

    class Meta:
        object_class = Domain
        allowed_methods = ('post',)
        resource_name = "whois"
        authentication = MultiAuthentication(CRITsApiKeyAuthentication(),
                                             CRITsSessionAuthentication())
        authorization = authorization.Authorization()
        serializer = CRITsSerializer()

    def obj_create(self, bundle, **kwargs):
        """
        Handles adding WhoIs entries to domains through the API.

        :param bundle: Bundle containing the information to create the Domain.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        :raises BadRequest: If a domain name is not provided or creation fails.
        """

        analyst = bundle.request.user.username
        domain = bundle.data.get('domain', None)
        date = bundle.data.get('date', None)
        whois = bundle.data.get('whois', None)

        if not domain:
            raise BadRequest('Need a Domain Name.')
        if not date:
            raise BadRequest('Need a date for this entry.')
        if not whois:
            raise BadRequest('Need whois data.')

        try:
            date = parse(date, fuzzy=True)
        except Exception, e:
            raise BadRequest('Cannot parse date: %s' % str(e))

        result = add_whois(domain, whois, date, analyst, True)

        content = {'return_code': 0,
                   'type': 'Domain',
                   'message': result.get('message', ''),
                   'id': result.get('id', '')}
        if result.get('id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'domains',
                                  'api_name': 'v1',
                                  'pk': result.get('id')})
            content['url'] = url
        if not result['success']:
            content['return_code'] = 1
        self.crits_response(content)
