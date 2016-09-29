import datetime

from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication

from crits.indicators.indicator import Indicator
from crits.indicators.handlers import handle_indicator_ind, activity_add
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class IndicatorResource(CRITsAPIResource):
    """
    Class to handle everything related to the Indicator API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Indicator
        allowed_methods = ('get', 'post', 'patch')
        resource_name = "indicators"
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

        return super(IndicatorResource, self).get_object_list(request,
                                                              Indicator)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating Indicators through the API.

        :param bundle: Bundle containing the information to create the Indicator.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        """

        analyst = bundle.request.user.username
        value = bundle.data.get('value', None)
        ctype = bundle.data.get('type', None)
        threat_type = bundle.data.get('threat_type', None)
        attack_type = bundle.data.get('attack_type', None)
        source = bundle.data.get('source', None)
        status = bundle.data.get('status', None)
        reference = bundle.data.get('reference', None)
        method = bundle.data.get('method', None)
        add_domain = bundle.data.get('add_domain', False)
        add_relationship = bundle.data.get('add_relationship', False)
        campaign = bundle.data.get('campaign', None)
        campaign_confidence = bundle.data.get('confidence', None)
        confidence = bundle.data.get('indicator_confidence', None)
        description = bundle.data.get('description', None)
        impact = bundle.data.get('indicator_impact', None)
        bucket_list = bundle.data.get('bucket_list', None)
        ticket = bundle.data.get('ticket', None)

        result =  handle_indicator_ind(value,
                                       source,
                                       ctype,
                                       threat_type,
                                       attack_type,
                                       analyst,
                                       status=status,
                                       method=method,
                                       reference=reference,
                                       add_domain=add_domain,
                                       add_relationship=add_relationship,
                                       campaign=campaign,
                                       campaign_confidence=campaign_confidence,
                                       confidence=confidence,
                                       description=description,
                                       impact=impact,
                                       bucket_list=bucket_list,
                                       ticket=ticket)

        content = {'return_code': 0,
                   'type': 'Indicator'}
        if result.get('message'):
            content['message'] = result.get('message')
        if result.get('objectid'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'indicators',
                                  'api_name': 'v1',
                                  'pk': result.get('objectid')})
            content['id'] = result.get('objectid')
            content['url'] = url
        if not result['success']:
            content['return_code'] = 1
        self.crits_response(content)

class IndicatorActivityResource(CRITsAPIResource):
    """
    Class to handle Indicator Activity.

    Currently supports POST.
    """

    class Meta:
        object_class = Indicator
        allowed_methods = ('post',)
        resource_name = "indicator_activity"
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

        return super(IndicatorActivityResource, self).get_object_list(request,
                                                                     Indicator)

    def obj_create(self, bundle, **kwargs):
        """
        Handles adding Indicator Activity through the API.

        :param bundle: Bundle containing the information to add the Activity.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        """

        analyst = bundle.request.user.username
        object_id = bundle.data.get('object_id', None)
        start_date = bundle.data.get('start_date', None)
        end_date = bundle.data.get('end_date', None)
        description = bundle.data.get('description', None)

        content = {'return_code': 1,
                   'type': 'Indicator'}

        if not object_id or not description:
            content['message'] = 'Must provide object_id and description.'
            self.crits_response(content)

        activity = {'analyst': analyst,
                    'start_date': start_date,
                    'end_date': end_date,
                    'description': description,
                    'date': datetime.datetime.now()}
        result = activity_add(object_id, activity)
        if not result['success']:
            content['message'] = result['message']
            self.crits_response(content)

        if result.get('message'):
            content['message'] = result.get('message')
        if result.get('id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'indicators',
                                  'api_name': 'v1',
                                  'pk': result.get('id')})
            content['id'] = result.get('id')
            content['url'] = url
        if result['success']:
            content['return_code'] = 0
        self.crits_response(content)
