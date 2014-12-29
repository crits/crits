from dateutil.parser import parse
from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest
from mongoengine.base import ValidationError

from crits.domains.domain import Domain
from crits.domains.handlers import add_new_domain, add_whois

from crits.core.handlers import source_remove_all, delete_id
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource
from crits.core.mongo_tools import validate_objectid
from crits.core.user_tools import is_admin, user_sources

import json


class DomainResource(CRITsAPIResource):
    """
    Domain API Resource Class.
    """

    class Meta:
        object_class = Domain
        allowed_methods = ('get', 'post', 'delete', 'patch')
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


    def delete_detail(self, request, **kwargs):
        """
        This will delete a specific domain ID record.

        The domain ID must be part of the URL (/api/v1/domains/{id}/)

        :param request: The incoming request.
        :type request: :class:`django.http.HttpRequest`
        :returns: HttpResponse.
        """
        content = {'return_code': 1,
                   'type': 'Domain'}

        username = request.user.username
        if not is_admin(username):
          content['message'] = 'You must be an admin to delete domains.'
          self.crits_response(content)

        path = request.path
        parts = path.split("/")
        id = parts[(len(parts) - 2)]

        if not validate_objectid(id):
          content['message'] = 'You must provide a valid domain ID.'
          self.crits_response(content)

        obj_type = Domain

        result, message = delete_id(username,obj_type,id)
        
        if result: 
          content['return_code'] = 0
        else:
          content['message'] = message

        self.crits_response(content)
   

    def patch_detail(self, request, **kwargs):
        """
        This will delete source references within the domain ID's record.

        The patch_detail method is for any modification to a record. The
        action parameter is hard coded to delete because that is the only
        modification that is currently supported.

        The data must be sent as JSON within the body of the request.

        This code assumes that the client has already deteremined whether there
        are multiple source associations.

        :param request: The incoming request.
        :type request: :class:`django.http.HttpRequest`
        :returns: HttpResponse.
        """

        content = {'return_code': 1,
                   'type': 'Domain'}

        analyst = request.user.username
        data = json.loads(request.body)
        action = "delete"

        if not is_admin(analyst):
          content['message'] = 'You must be an admin to modify domains.'
          self.crits_response(content)

        path = request.path
        parts = path.split("/")
        id = parts[(len(parts) - 2)]

        if not validate_objectid(id):
          content['message'] = 'You must provide a valid domain ID.'
          self.crits_response(content)

        sources = user_sources(analyst)
        obj_type = Domain
        doc = obj_type.objects(id=id,source__name__in=sources).first()

        if not doc:
          content['message'] = 'The provided ID is not available to the provided account.'
          self.crits_response(content)

        result = {}

        source = ""
        try:
          source = data.get("source")
        except KeyError, e:
          source = ""

        if source == None or source == "":
            content['message'] = 'A source must be provided.'
            self.crits_response(content)

        if source != None and source != "":
          if action == "delete":
            if not (source in sources):
                 content['message'] = 'You are not authorized to remove this source'
                 self.crits_response(content)
            result = source_remove_all("Domain",id,source,analyst)

            if result == None:
              content['message'] = 'Could not remove source.'
              self.crits_response(content)

            if not result['success']:
              if result.get('message'):
                 content['message'] = result.get('message')
              else:
                 content['message'] = 'Could not find source.'
              self.crits_response(content)

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
