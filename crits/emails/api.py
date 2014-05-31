from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.emails.email import Email
from crits.emails.handlers import handle_pasted_eml, handle_yaml, handle_eml
from crits.emails.handlers import handle_email_fields, handle_msg
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class EmailResource(CRITsAPIResource):
    """
    Class to handle everything related to the Email API.

    Currently supports GET and POST.
    """

    class Meta:
        queryset = Email.objects.all()
        allowed_methods = ('get', 'post')
        resource_name = "emails"
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

        return super(EmailResource, self).get_object_list(request, Email)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating Emails through the API.

        :param bundle: Bundle containing the information to create the Campaign.
        :type bundle: Tastypie Bundle object.
        :returns: Bundle object.
        :raises BadRequest: If a type_ is not provided or creation fails.
        """

        analyst = bundle.request.user.username
        type_ = bundle.data.get('upload_type', None)
        if not type_:
            raise BadRequest('You must specify the upload type.')
        elif type_ not in ('eml', 'msg', 'raw', 'yaml', 'fields'):
            raise BadRequest('Unknown or unsupported upload type.')

        # Remove this so it doesn't get included with the fields upload
        del bundle.data['upload_type']
        result = None

        # Extract common information
        source = bundle.data.get('source', None)
        reference = bundle.data.get('reference', None)
        campaign = bundle.data.get('campaign', None)
        confidence = bundle.data.get('confidence', None)

        if type_ == 'eml':
            file_ = bundle.data.get('filedata', None)
            if not file_:
                raise BadRequest('No file uploaded.')
            filedata = file_.read()
            result = handle_eml(filedata, source, reference,
                                analyst, 'Upload', campaign,
                                confidence)
        if type_ == 'msg':
            raw_email = bundle.data.get('filedata', None)
            password = bundle.data.get('password', None)
            result = handle_msg(raw_email,
                                source,
                                reference,
                                analyst,
                                'Upload',
                                password,
                                campaign,
                                confidence)
        if type_ == 'raw':
            raw_email = bundle.data.get('filedata', None)
            result = handle_pasted_eml(raw_email,
                                       source,
                                       reference,
                                       analyst,
                                       'Upload',
                                       campaign,
                                       confidence)
        if type_ == 'yaml':
            yaml_data = bundle.data.get('filedata', None)
            email_id = bundle.data.get('email_id', None)
            save_unsupported = bundle.data.get('save_unsupported', False)
            result = handle_yaml(yaml_data,
                                 source,
                                 reference,
                                 analyst,
                                 'Upload',
                                 email_id,
                                 save_unsupported,
                                 campaign,
                                 confidence)
        if type_ == 'fields':
            fields = bundle.data
            result = handle_email_fields(fields,
                                         analyst,
                                         'Upload')
        if not result:
            raise BadRequest('No upload type found.')
        if not result['status']:
            raise BadRequest(result['reason'])
        else:
            return bundle
