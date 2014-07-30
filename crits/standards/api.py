from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.standards.handlers import import_standards_doc
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource




class StandardsResource(CRITsAPIResource):
    """
    Class to handle everything related to the Standards API.

    Currently supports  POST.
    """

    class Meta:
        allowed_methods = ( 'post',)
        resource_name = "standards"
        authentication = MultiAuthentication(CRITsApiKeyAuthentication(),
                                             CRITsSessionAuthentication())
        authorization = authorization.Authorization()
        serializer = CRITsSerializer()




    def obj_create(self, bundle, **kwargs):
        """
        Handles creating STIX documents through the API.

        :param bundle: Bundle containing the information to create the Campaign.
        :type bundle: Tastypie Bundle object.
        :returns: Bundle object.
        :raises BadRequest: If a type_ is not provided or creation fails.
        """

        analyst = bundle.request.user.username
        type_ = bundle.data.get('upload_type', None)


        if not type_:
            raise BadRequest('You must specify the upload type.')
        elif type_ not in ('stix'):
            raise BadRequest('Unknown or unsupported upload type. '+type_)

        # Remove this so it doesn't get included with the fields upload
        del bundle.data['upload_type']
        result = None

        # Extract common information

        source = bundle.data.get('source', None)
        makeevent = bundle.data.get('make_event',False)

        if not source:
            raise BadRequest('No Source was specified')

        file_ = bundle.data.get('filedata', None)
        if not file_:
            raise BadRequest('No file uploaded.')
        filedata = file_.read()
        result = import_standards_doc(filedata,
                    analyst, 
                    "Upload",
                    make_event = makeevent,
                    ref = reference,
                    source = source)


        if not result:
            raise BadRequest('No upload type found.')
        if not result['success']:
            raise BadRequest(result['reason']+"SAB HA HA")
        else:
            return bundle
