from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication

from crits.domains.domain import Domain
from crits.domains.handlers import add_new_domain
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class DomainResource(CRITsAPIResource):
    """
    Domain API Resource Class.
    """

    class Meta:
        object_class = Domain
        allowed_methods = ('get', 'post', 'patch')
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
        ip_type = bundle.data.get('ip_type', None)
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
                'ip_type': ip_type,
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
