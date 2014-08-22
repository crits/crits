from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.samples.sample import Sample
from crits.samples.handlers import handle_uploaded_file
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class SampleResource(CRITsAPIResource):
    """
    Class to handle everything related to the Sample API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Sample
        allowed_methods = ('get', 'post')
        resource_name = "samples"
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

        return super(SampleResource, self).get_object_list(request, Sample)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating Samples through the API.

        :param bundle: Bundle containing the information to create the Sample.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        :raises BadRequest: If filedata is not provided or creation fails.
        """

        analyst = bundle.request.user.username
        type_ = bundle.data.get('upload_type', None)
        if not type_:
            raise BadRequest('Must provide an upload type.')
        if type_ not in ('metadata', 'file'):
            raise BadRequest('Not a valid upload type.')
        if type_ == 'metadata':
            filename = bundle.data.get('filename', None)
            md5 = bundle.data.get('md5', None)
            password = None
            filedata = None
        elif type_ == 'file':
            md5 = None
            password = bundle.data.get('password', None)
            file_ = bundle.data.get('filedata', None)
            if not file_:
                raise BadRequest("Upload type of 'file' but no file uploaded.")
            filedata = file_
            filename = None

        campaign = bundle.data.get('campaign', None)
        confidence = bundle.data.get('confidence', None)
        source = bundle.data.get('source', None)
        method = bundle.data.get('method', "")
        reference = bundle.data.get('reference', None)
        file_format = bundle.data.get('file_format', None)
        related_md5 = bundle.data.get('related_md5', None)
        related_id = bundle.data.get('related_id', None)
        related_type = bundle.data.get('related_type', None)
        bucket_list = bundle.data.get('bucket_list', None)
        ticket = bundle.data.get('ticket', None)

        sample_md5 = handle_uploaded_file(filedata,
                                          source,
                                          method,
                                          reference,
                                          file_format,
                                          password,
                                          user=analyst,
                                          campaign=campaign,
                                          confidence=confidence,
                                          related_md5 = related_md5,
                                          related_id = related_id,
                                          related_type = related_type,
                                          filename=filename,
                                          md5=md5,
                                          bucket_list=bucket_list,
                                          ticket=ticket,
                                          is_return_only_md5=False)

        content = {'return_code': 0,
                   'type': 'Sample'}
        result = {'success': False}

        if len(sample_md5) > 0:
            result = sample_md5[0]
            if result.get('success') is False:
                raise BadRequest('Must provide a related type ')
            content['message'] = result.get('message', '')
            content['id'] = str(result.get('object').id)
            if content.get('id'):
                url = reverse('api_dispatch_detail',
                            kwargs={'resource_name': 'samples',
                                    'api_name': 'v1',
                                    'pk': content.get('id')})
                content['url'] = url
        if not result['success']:
            content['return_code'] = 1
            content['message'] = "Could not create Sample for unknown reason."
        self.crits_response(content)
