from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

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
        queryset = RelationshipType.objects.all()
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
        :returns: Bundle object.
        :raises BadRequest: If necessary data is not provided or creation fails.

        """
        analyst = bundle.request.user.username
        left_type = bundle.data.get('left_type', None)
        left_id = bundle.data.get('left_id', None)
        right_type = bundle.data.get('right_type', None)
        right_id = bundle.data.get('right_id', None)
        rel_type = bundle.data.get('rel_type', None)
        rel_date = bundle.data.get('rel_date', None)

        if (not left_type
            or not left_id
            or not right_type
            or not right_id
            or not rel_type):
            raise BadRequest('Need all of the relationship information.')
        result = forge_relationship(left_type=left_type,
                                    left_id=left_id,
                                    right_type=right_type,
                                    right_id=right_id,
                                    rel_type=rel_type,
                                    rel_date=rel_date,
                                    analyst=analyst,
                                    get_rels=False)
        if not result['success']:
            raise BadRequest(result['message'])
        else:
            return bundle
