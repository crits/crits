from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.pcaps.pcap import PCAP
from crits.pcaps.handlers import handle_pcap_file
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class PCAPResource(CRITsAPIResource):
    """
    Class to handle everything related to the PCAP API.

    Currently supports GET and POST.
    """

    class Meta:
        queryset = PCAP.objects.all()
        allowed_methods = ('get', 'post')
        resource_name = "pcaps"
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

        return super(PCAPResource, self).get_object_list(request, PCAP)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating PCAPs through the API.

        :param bundle: Bundle containing the information to create the PCAP.
        :type bundle: Tastypie Bundle object.
        :returns: Bundle object.
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

        result = handle_pcap_file(filename,
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

        if result['success']:
            return bundle
        else:
            raise BadRequest(result['message'])
