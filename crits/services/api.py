from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.services.handlers import add_result, add_log, finish_task
from crits.services.service import CRITsService
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class ServiceResource(CRITsAPIResource):
    """
    Class to handle everything related to the Services API.

    Currently supports POST.
    """

    class Meta:
        object_class = CRITsService
        allowed_methods = ('post',)
        resource_name = "services"
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

        return super(ServiceResource, self).get_object_list(request,
                                                            CRITsService,
                                                            False)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating service result entries through the API.

        :param bundle: Bundle containing the service results to add.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        :raises BadRequest: If necessary data is not provided or creation fails.

        """
        analyst = bundle.request.user.username
        object_type = bundle.data.get('object_type', None)
        object_id = bundle.data.get('object_id', None)
        analysis_id = bundle.data.get('analysis_id', None)
        result = bundle.data.get('result', None)
        result_type = bundle.data.get('result_type', None)
        result_subtype = bundle.data.get('result_subtype', None)
        log_message = bundle.data.get('log_message', None)
        log_level = bundle.data.get('log_level', 'info')
        status = bundle.data.get('status', None)
        finish = bundle.data.get('finish', False)

        success = True
        message = ""

        if not object_type or not object_id or not analysis_id:
            raise BadRequest('Need an object type, object id, and analysis id.')
        if result:
            if not result_type or not result_subtype:
                raise BadRequest('When adding a result, also need type and subtype')
            result = add_result(object_type, object_id, analysis_id,
                                result, result_type, result_subtype, analyst)
            if not result['success']:
                message += ", %s" % result['message']
                success = False
        if log_message:
            result = add_log(object_type, object_id, analysis_id,
                             log_message, log_level, analyst)
            if not result['success']:
                message += ", %s" % result['message']
                success = False
        if finish:
            result = finish_task(object_type, object_id, analysis_id,
                                 status, analyst)
            if not result['success']:
                message += ", %s" % result['message']
                success = False

        content = {'return_code': 0,
                   'type': object_type,
                   'message': message,
                   'id': object_id}
        rname = self.resource_name_from_type(object_type)
        url = reverse('api_dispatch_detail',
                        kwargs={'resource_name': rname,
                                'api_name': 'v1',
                                'pk': object_id})
        content['url'] = url
        if not success:
            content['return_code'] = 1
        self.crits_response(content)
