from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.standards.handlers import import_standards_doc
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource
import logging
import pickle




class StandardsResource(CRITsAPIResource):
    """
    Class to handle everything related to the Email API.

    Currently supports GET and POST.
    """

    class Meta:
        #queryset = Email.objects.all()
        #allowed_methods = ('get', 'post')
        allowed_methods = ( 'post')
        resource_name = "standards"
        authentication = MultiAuthentication(CRITsApiKeyAuthentication(),
                                             CRITsSessionAuthentication())
        authorization = authorization.Authorization()
        serializer = CRITsSerializer()


   

# SAB  No get for this rount

    def get_object_list(self, request):
        """
        Use the CRITsAPIResource to get our objects but provide the class to get
        the objects from.

        :param request: The incoming request.
        :type request: :class:`django.http.HttpRequest`
        :returns: Resulting objects in the specified format (JSON by default).
        """

        return None
#        return super(StandardsResource, self).get_object_list(request, None)

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

        f.write(str(type_)+"is the type sent in\n")
        # Remove this so it doesn't get included with the fields upload
        del bundle.data['upload_type']
        result = None

        # Extract common information
        source = bundle.data.get('source', None)
        reference = bundle.data.get('reference', None)
        campaign = bundle.data.get('campaign', None)
        confidence = bundle.data.get('confidence', None)

        if type_ == 'stix':
            file_ = bundle.data.get('filedata', None)
            if not file_:
                raise BadRequest('No file uploaded.')
            filedata = file_.read()
            result = import_standards_doc(filedata,
                            analyst, 
                            "Upload",
                            make_event=True,
                            ref = reference,
                            source = source)
#

        if not result:
            raise BadRequest('No upload type found.')
        if not result['success']:
            raise BadRequest(result['reason']+"SAB HA HA")
        else:
            return bundle
