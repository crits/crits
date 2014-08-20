from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.certificates.certificate import Certificate
from crits.certificates.handlers import handle_cert_file
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class CertificateResource(CRITsAPIResource):
    """
    Class to handle everything related to the Certificate API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Certificate
        allowed_methods = ('get', 'post')
        resource_name = "certificates"
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

        return super(CertificateResource, self).get_object_list(request,
                                                                Certificate)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating Certificates through the API.

        :param bundle: Bundle containing the information to create the Certificate.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        :raises BadRequest: If filedata is not provided or creation fails.

        """

        analyst = bundle.request.user.username
        file_ = bundle.data.get('filedata', None)
        if not file_:
            raise BadRequest("Upload type of 'file' but no file uploaded.")
        filedata = file_.read()
        filename = str(file_)

        source = bundle.data.get('source', None)
        method = bundle.data.get('method', None)
        description = bundle.data.get('reference', None)
        relationship = bundle.data.get('relationship', None)
        parent_id = bundle.data.get('related_id', None)
        parent_md5 = bundle.data.get('related_md5', None)
        parent_type = bundle.data.get('related_type', None)
        bucket_list = bundle.data.get('bucket_list', None)
        ticket = bundle.data.get('ticket', None)

        result = handle_cert_file(filename,
                                  filedata,
                                  source,
                                  analyst,
                                  description,
                                  parent_id=parent_id,
                                  parent_md5=parent_md5,
                                  parent_type = parent_type,
                                  method=method,
                                  relationship=relationship,
                                  bucket_list=bucket_list,
                                  ticket=ticket)

        content = {'return_code': 0,
                   'type': 'Certificate',
                   'message': result.get('message', ''),
                   'id': result.get('id', '')}
        if result.get('id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'certificates',
                                  'api_name': 'v1',
                                  'pk': result.get('id')})
            content['url'] = url
        if not result['success']:
            content['return_code'] = 1
        self.crits_response(content)
