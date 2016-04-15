from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication

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
        allowed_methods = ('get', 'post', 'patch')
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
        """

        analyst = bundle.request.user.username
        type_ = bundle.data.get('upload_type', None)

        content = {'return_code': 1,
                   'type': 'Sample'}

        if not type_:
            content['message'] = 'Must provide an upload type.'
            self.crits_response(content)
        if type_ not in ('metadata', 'file'):
            content['message'] = 'Not a valid upload type.'
            self.crits_response(content)
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
                content['message'] = "Upload type of 'file' but no file uploaded."
                self.crits_response(content)
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
        backdoor_name = bundle.data.get('backdoor_name', None)
        backdoor_version = bundle.data.get('backdoor_version', None)
        bucket_list = bundle.data.get('bucket_list', None)
        ticket = bundle.data.get('ticket', None)
        sha1 = bundle.data.get('sha1', None)
        sha256 = bundle.data.get('sha256', None)
        size = bundle.data.get('size', None)
        mimetype = bundle.data.get('mimetype', None)

        if ((related_id and not related_type) or
            (related_type and not related_id)):
            content['message'] = "Must specify related_type and related_id"
            self.crits_response(content)

        sample_md5 = handle_uploaded_file(filedata,
                                          source,
                                          method,
                                          reference,
                                          file_format,
                                          password,
                                          user=analyst,
                                          campaign=campaign,
                                          confidence=confidence,
                                          related_md5=related_md5,
                                          related_id=related_id,
                                          related_type=related_type,
                                          filename=filename,
                                          md5=md5,
                                          sha1=sha1,
                                          sha256=sha256,
                                          size=size,
                                          mimetype=mimetype,
                                          bucket_list=bucket_list,
                                          ticket=ticket,
                                          is_return_only_md5=False,
                                          backdoor_name=backdoor_name,
                                          backdoor_version=backdoor_version)

        result = {'success': False}

        if len(sample_md5) > 0:
            result = sample_md5[0]
            if result.get('message'):
                content['message'] = result.get('message')
            if result.get('object'):
                content['id'] = str(result.get('object').id)
            if content.get('id'):
                url = reverse('api_dispatch_detail',
                            kwargs={'resource_name': 'samples',
                                    'api_name': 'v1',
                                    'pk': content.get('id')})
                content['url'] = url
        else:
            content['message'] = "Could not create Sample for unknown reason."

        if result['success']:
            content['return_code'] = 0
        self.crits_response(content)
