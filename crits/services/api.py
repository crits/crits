import json
from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.services.handlers import add_result, add_results, add_log, finish_task
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

        """
        analyst = bundle.request.user.username
        object_type = bundle.data.get('object_type', None)
        object_id = bundle.data.get('object_id', None)
        analysis_id = bundle.data.get('analysis_id', None)
        result = bundle.data.get('result', None)
        result_type = bundle.data.get('result_type', None)
        result_subtype = bundle.data.get('result_subtype', None)
        result_is_batch = bundle.data.get('result_is_batch', False)
        log_message = bundle.data.get('log_message', None)
        log_level = bundle.data.get('log_level', 'info')
        status = bundle.data.get('status', None)
        finish = bundle.data.get('finish', False)

        success = True
        message = ""

        content = {'return_code': 1,
                   'type': object_type}

        if not object_type or not object_id or not analysis_id:
            content['message'] = 'Need an object type, object id, and analysis id.'
            self.crits_response(content)
        if result:
            if not result_type or not result_subtype:
                content['message'] = 'When adding a result, also need type and subtype'
                self.crits_response(content)

            if not result_is_batch:
                result = add_result(object_type, object_id, analysis_id,
                                    result, result_type, result_subtype, analyst)
            else:
                result_list = json.loads(result)
                result_type_list = json.loads(result_type)
                result_subtype_list = json.loads(result_subtype)

                if not (len(result_list) == len(result_type_list) == len(result_subtype_list)):
                    content['message'] = 'When adding results in batch result, result_type, and result_subtype must have the same length!'
                    self.crits_response(content)
                
                result = add_results(object_type, object_id, analysis_id, result_list,
                                     result_type_list, result_subtype_list, analyst)

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

        content['message'] = message
        content['id'] = object_id
        rname = self.resource_name_from_type(object_type)
        url = reverse('api_dispatch_detail',
                        kwargs={'resource_name': rname,
                                'api_name': 'v1',
                                'pk': object_id})
        content['url'] = url
        if success:
            content['return_code'] = 0
        self.crits_response(content)
