from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication

from crits.signatures.signature import Signature
from crits.signatures.handlers import handle_signature_file
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource

from crits.vocabulary.acls import SignatureACL

class SignatureResource(CRITsAPIResource):
    """
    Class to handle everything related to the Signature API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Signature
        allowed_methods = ('get', 'post', 'patch')
        resource_name = "signatures"
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

        return super(SignatureResource, self).get_object_list(request, Signature)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating Signatures through the API.

        :param bundle: Bundle containing the information to create the RawData.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.

        """

        user = bundle.request.user
        content = {'return_code': 1,
                   'type': 'Signature'}
        data = bundle.data.get('data', None)
        source = bundle.data.get('source', None)
        description = bundle.data.get('description', '')
        tlp = bundle.data.get('tlp', 'amber')
        title = bundle.data.get('title', None)
        data_type = bundle.data.get('data_type', None)
        data_type_min_version = bundle.data.get('data_type_min_version', None)
        data_type_max_version = bundle.data.get('data_type_max_version', None)
        data_type_dependency = bundle.data.get('data_type_dependency', None)
        link_id = bundle.data.get('link_id', None)
        copy_rels = bundle.data.get('copy_relationships', False)
        method = bundle.data.get('method', None) or 'Upload'
        reference = bundle.data.get('reference', None)
        bucket_list = bundle.data.get('bucket_list', None)
        ticket = bundle.data.get('ticket', None)

        if not title:
            content['message'] = "Must provide a title."
            self.crits_response(content)
        if not data_type:
            content['message'] = "Must provide a data type."
            self.crits_response(content)

        if not user.has_access_to(SignatureACL.WRITE):
            content['message'] = 'User does not have permission to create Object.'
            self.crits_response(content)

        result = handle_signature_file(data, source, user,
                                      description, title, data_type,
                                      data_type_min_version,
                                      data_type_max_version,
                                      data_type_dependency,link_id,
                                      source_method=method,
                                      source_reference=reference,
                                      source_tlp=tlp,
                                      copy_rels=copy_rels,
                                      bucket_list=bucket_list,
                                      ticket=ticket)

        if result.get('message'):
            content['message'] = result.get('message')
        if result.get('_id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'signatures',
                                  'api_name': 'v1',
                                  'pk': str(result.get('_id'))})
            content['url'] = url
            content['id'] = str(result.get('_id'))
        if result['success']:
            content['return_code'] = 0
        self.crits_response(content)
