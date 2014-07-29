from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.ips.ip import IP
from crits.ips.handlers import ip_add_update
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class IPResource(CRITsAPIResource):
    """
    Class to handle everything related to the IP API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = IP
        allowed_methods = ('get', 'post')
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
        :returns: Bundle object.
        :raises BadRequest: If creation fails.
        """

        analyst = bundle.request.user.username
        data = bundle.data
        ip = data['ip']
        name = data['source']
        reference = data['reference']
        method = data['method']
        campaign = data['campaign']
        confidence = data['confidence']
        ip_type = data['ip_type']
        add_indicator = data.get('add_indicator', False)
        indicator_reference = data.get('indicator_reference')
        bucket_list = data.get('bucket_list', None)
        ticket = data.get('ticket', None)

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
        if 'message' in result:
            raise BadRequest(result['message'])
        else:
            return bundle
