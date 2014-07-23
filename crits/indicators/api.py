import datetime

from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

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
        allowed_methods = ('get', 'post')
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
        :returns: Bundle object.
        :raises BadRequest: If a campaign name is not provided or creation fails.
        """

        analyst = bundle.request.user.username
        value = bundle.data.get('value', None)
        ctype = bundle.data.get('type', None)
        source = bundle.data.get('source', None)
        reference = bundle.data.get('reference', None)
        method = bundle.data.get('method', None)
        add_domain = bundle.data.get('add_domain', False)
        add_relationship = bundle.data.get('add_relationship', False)
        campaign = bundle.data.get('campaign', None)
        campaign_confidence = bundle.data.get('confidence', None)
        confidence = bundle.data.get('indicator_confidence', None)
        impact = bundle.data.get('indicator_impact', None)
        bucket_list = bundle.data.get('bucket_list', None)
        ticket = bundle.data.get('ticket', None)

        if analyst:
            result =  handle_indicator_ind(value,
                                           source,
                                           reference,
                                           ctype,
                                           analyst,
                                           method,
                                           add_domain,
                                           add_relationship,
                                           campaign,
                                           campaign_confidence,
                                           confidence,
                                           impact,
                                           bucket_list,
                                           ticket)
            if not result['success']:
                raise BadRequest(result['message'])
            else:
                return bundle
        else:
            raise BadRequest('You must be an authenticated user!')

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
        :returns: Bundle object.
        :raises BadRequest: If a campaign name is not provided or creation fails.
        """

        analyst = bundle.request.user.username
        object_id = bundle.data.get('object_id', None)
        start_date = bundle.data.get('start_date', None)
        end_date = bundle.data.get('end_date', None)
        description = bundle.data.get('description', None)

        activity = {'analyst': analyst,
                    'start_date': start_date,
                    'end_date': end_date,
                    'description': description,
                    'date': datetime.datetime.now()}
        result = activity_add(object_id, activity)
        if not result['success']:
            raise BadRequest(result['message'])
        else:
            return bundle
