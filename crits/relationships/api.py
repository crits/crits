from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication

from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource
from crits.core.crits_mongoengine import RelationshipType
from crits.relationships.handlers import forge_relationship


class RelationshipResource(CRITsAPIResource):
    """
    Class to handle everything related to the Relationship API.

    Currently supports POST.
    """

    class Meta:
        object_class = RelationshipType
        allowed_methods = ('post',)
        resource_name = "relationships"
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

        return super(RelationshipResource, self).get_object_list(request,
                                                                 RelationshipType,
                                                                 False)

    def obj_create(self, bundle, **kwargs):
        """
        Handles forging relationships through the API.

        :param bundle: Bundle containing the relationship information.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.

        """
        analyst = bundle.request.user.username
        left_type = bundle.data.get('left_type', None)
        left_id = bundle.data.get('left_id', None)
        right_type = bundle.data.get('right_type', None)
        right_id = bundle.data.get('right_id', None)
        rel_type = bundle.data.get('rel_type', None)
        rel_date = bundle.data.get('rel_date', None)
        rel_confidence = bundle.data.get('rel_confidence', 'unknown')
        rel_reason = bundle.data.get('rel_reason', 'N/A')

        content = {'return_code': 1,
                   'type': left_type}

        if (not left_type
            or not left_id
            or not right_type
            or not right_id
            or not rel_type):
            content['message'] = 'Need all of the relationship information.'
            self.crits_response(content)

        if rel_confidence not in ('unknown', 'low', 'medium', 'high'):
            content['message'] = 'Bad relationship confidence.'
            self.crits_response(content)

        result = forge_relationship(left_type=left_type,
                                    left_id=left_id,
                                    right_type=right_type,
                                    right_id=right_id,
                                    rel_type=rel_type,
                                    rel_date=rel_date,
                                    analyst=analyst,
                                    rel_confidence=rel_confidence,
                                    rel_reason=rel_reason,
                                    get_rels=False)

        if result.get('message'):
            content['message'] = result.get('message')

        content['id'] = left_id
        rname = self.resource_name_from_type(left_type)
        url = reverse('api_dispatch_detail',
                        kwargs={'resource_name': rname,
                                'api_name': 'v1',
                                'pk': left_id})
        content['url'] = url
        if result['success']:
            content['return_code'] = 0
        self.crits_response(content)
