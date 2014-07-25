from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.actors.actor import Actor
from crits.actors.handlers import add_new_actor
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class ActorResource(CRITsAPIResource):
    """
    Class to handle everything related to the Actor API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Actor
        allowed_methods = ('get', 'post')
        resource_name = "actors"
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

        return super(ActorResource, self).get_object_list(request, Actor)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating Actors through the API.

        :param bundle: Bundle containing the information to create the Actor.
        :type bundle: Tastypie Bundle object.
        :returns: Bundle object.
        :raises BadRequest: If creation fails.
        """

        analyst = bundle.request.user.username
        data = bundle.data
        name = data['name']
        aliases = data['aliases']
        description = data['description']
        source = data['source']
        reference = data['reference']
        method = data['method']
        campaign = data['campaign']
        confidence = data['confidence']
        bucket_list = data.get('bucket_list', None)
        ticket = data.get('ticket', None)

        result = add_new_actor(name,
                               aliases,
                               description=description,
                               source=source,
                               source_method=method,
                               source_reference=reference,
                               campaign=campaign,
                               confidence=confidence,
                               analyst=analyst,
                               bucket_list=bucket_list,
                               ticket=ticket)
        if 'message' in result:
            raise BadRequest(result['message'])
        else:
            return bundle
