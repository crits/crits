from dateutil.parser import parse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.domains.domain import Domain
from crits.domains.handlers import add_new_domain, add_whois
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class DomainResource(CRITsAPIResource):
    """
    Domain API Resource Class.
    """

    class Meta:
        object_class = Domain
        allowed_methods = ('get', 'post')
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
        :returns: Bundle object.
        :raises BadRequest: If a domain name is not provided or creation fails.
        """

        analyst = bundle.request.user.username
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

        if analyst:
            if not domain:
                raise BadRequest('Need a Domain Name.')
            # The empty list is necessary. The function requires a list of
            # non-fatal errors so it can be added to if any other errors
            # occur. Since we have none, we pass the empty list.
            (result, errors, retVal) =  add_new_domain(data,
                                                       request,
                                                       [])
            if errors:
                if not 'message' in retVal:
                    retVal['message'] = ""
                elif not isinstance(retVal['message'], basestring):
                    retVal['message'] = str(retVal['message'])
                for e in errors:
                    retVal['message'] += " %s " % str(e)
                raise BadRequest(retVal['message'])
            else:
                return bundle
        else:
            raise BadRequest('You must be an authenticated user!')


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
        :returns: Bundle object.
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
        if not result['success']:
            raise BadRequest('Could not add whois: %s' % str(result['message']))
        else:
            return bundle
