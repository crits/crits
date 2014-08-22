from django.core.urlresolvers import reverse
from mongoengine import Document
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.standards.handlers import import_standards_doc
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource
from crits.core.crits_mongoengine import CritsDocument


class StandardsObject(CritsDocument, Document):
    """
    Class to store data if we ever decide to make this support GET
    """

class StandardsResource(CRITsAPIResource):
    """
    Class to handle everything related to the Standards API.

    Currently supports  POST.
    """

    class Meta:
        object_class = StandardsObject
        allowed_methods = ('post',)
        resource_name = "standards"
        authentication = MultiAuthentication(CRITsApiKeyAuthentication(),
                                             CRITsSessionAuthentication())
        authorization = authorization.Authorization()
        serializer = CRITsSerializer()


    def obj_create(self, bundle, **kwargs):
        """
        Handles creating STIX documents through the API.

        :param bundle: Bundle to create the records associated with this STIX document.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        """

        analyst = bundle.request.user.username
        type_ = bundle.data.get('upload_type', None)

        content = {'return_code': 1,
                   'imported': [],
                   'failed': []}

        if not type_:
            content['message'] = 'You must specify the upload type.'
            self.crits_response(content)
        elif type_ not in ('file', 'xml'):
            content['message'] = 'Unknown or unsupported upload type. ' + type_
            self.crits_response(content)

        # Remove this so it doesn't get included with the fields upload
        del bundle.data['upload_type']

        # Extract common information
        source = bundle.data.get('source', None)
        method = bundle.data.get('method', None)
        reference = bundle.data.get('reference', None)
        me = bundle.data.get('make_event', False)  # default to False for the event

        if not source:
            content['message'] = 'No Source was specified'
            self.crits_response(content)

        if type_ == 'xml':
            filedata = bundle.data.get('xml', None)
        elif type_ == 'file':
            file_ = bundle.data.get('filedata', None)
            filedata = file_.read()
        if not filedata:
            content['message'] = 'No STIX content uploaded.'
            self.crits_response(content)
        result = import_standards_doc(filedata,
                                      analyst,
                                      method,
                                      make_event = me,
                                      ref = reference,
                                      source = source)

        if len(result['imported']):
            for i in result['imported']:
                d = {}
                otype = i[0]
                obj = i[1]
                rname = self.resource_name_from_type(otype)
                url = reverse('api_dispatch_detail',
                            kwargs={'resource_name': rname,
                                    'api_name': 'v1',
                                    'pk': str(obj.id)})
                d['url'] = url
                d['type'] = otype
                d['id'] = str(obj.id)
                content['imported'].append(d)
        if len(result['failed']):
            for f in result['failed']:
                d = {'type': f[1],
                     'message': f[0]}
                content['failed'].append(d)
        if result['success']:
            content['return_code'] = 0
        self.crits_response(content)
