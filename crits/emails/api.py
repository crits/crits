try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication

from crits.emails.email import Email
from crits.emails.handlers import handle_pasted_eml, handle_yaml, handle_eml
from crits.emails.handlers import handle_email_fields, handle_msg
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource

from crits.vocabulary.acls import EmailACL


class EmailResource(CRITsAPIResource):
    """
    Class to handle everything related to the Email API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Email
        allowed_methods = ('get', 'post', 'patch')
        resource_name = "emails"
        ordering = ("from", "recip", "subject", "isodate", "status", 
                    "favorite", "id")
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
        :returns: HttpResponse.
        """

        user = bundle.request.user
        type_ = bundle.data.get('upload_type', None)

        content = {'return_code': 1,
                   'type': 'Email',
                   'message': ''}

        if not type_:
            content['message'] = 'You must specify the upload type.'
            self.crits_response(content)
        elif type_ not in ('eml', 'msg', 'raw', 'yaml', 'fields'):
            content['message'] = 'Unknown or unsupported upload type.'
            self.crits_response(content)

        # Remove this so it doesn't get included with the fields upload
        del bundle.data['upload_type']
        result = None

        # Extract common information
        source = bundle.data.get('source_name', None)
        method = bundle.data.get('source_method', '')
        reference = bundle.data.get('source_reference', None)
        tlp = bundle.data.get('source_tlp', 'amber')
        campaign = bundle.data.get('campaign', None)
        confidence = bundle.data.get('confidence', None)
        bucket_list = bundle.data.get('bucket_list', None)
        ticket = bundle.data.get('ticket', None)

        if method:
            method = " - " + method

        if not user.has_access_to(EmailACL.WRITE):
            content['success'] = False
            content['message'] = 'User does not have permission to create Object.'

            self.crits_response(content)

        if type_ == 'eml':
            file_ = bundle.data.get('filedata', None)
            if not file_:
                content['message'] = 'No file uploaded.'
                self.crits_response(content)
            filedata = file_.read()
            result = handle_eml(data=filedata, sourcename=source, reference=reference,
                                user=user, method='EML Upload' + method, tlp=tlp, campaign=campaign,
                                confidence=confidence, bucket_list=bucket_list, ticket=ticket)
        if type_ == 'msg':
            raw_email = bundle.data.get('filedata', None)
            password = bundle.data.get('password', None)

            result = handle_msg(raw_email,
                                source,
                                reference,
                                'Outlook MSG Upload' + method,
                                tlp,
                                user,
                                password,
                                campaign,
                                confidence,
                                bucket_list=bucket_list,
                                ticket=ticket)
        if type_ == 'raw':
            raw_email = bundle.data.get('filedata', None)
            result = handle_pasted_eml(raw_email,
                                       source,
                                       reference,
                                       'Raw Upload' + method,
                                       tlp,
                                       user,
                                       campaign,
                                       confidence,
                                       bucket_list=bucket_list,
                                       ticket=ticket)
        if type_ == 'yaml':
            yaml_data = bundle.data.get('filedata', None)
            email_id = bundle.data.get('email_id', None)
            save_unsupported = bundle.data.get('save_unsupported', False)
            result = handle_yaml(yaml_data,
                                 source,
                                 reference,
                                 'YAML Upload' + method,
                                 tlp,
                                 user,
                                 email_id,
                                 save_unsupported,
                                 campaign,
                                 confidence,
                                 bucket_list=bucket_list,
                                 ticket=ticket)
        if type_ == 'fields':
            fields = bundle.data
            # Strip these so they don't get put in unsupported_attrs.
            del fields['username']
            del fields['api_key']
            result = handle_email_fields(fields,
                                         user,
                                         'Fields Upload')

        if result.get('message'):
            content['message'] = result.get('message')
        if result.get('reason'):
            content['message'] += result.get('reason')
        if result.get('obj_id'):
            content['id'] = str(result.get('obj_id', ''))
        elif result.get('object'):
            content['id'] = str(result.get('object').id)
        if content.get('id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'emails',
                                  'api_name': 'v1',
                                  'pk': content.get('id')})
            content['url'] = url
        if result['status']:
            content['return_code'] = 0
        self.crits_response(content)
