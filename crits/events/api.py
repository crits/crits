from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication
from tastypie.exceptions import BadRequest

from crits.events.event import Event, EventType
from crits.events.handlers import add_new_event
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource


class EventResource(CRITsAPIResource):
    """
    Class to handle everything related to the Event API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Event
        allowed_methods = ('get', 'post')
        resource_name = "events"
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

        return super(EventResource, self).get_object_list(request, Event)

    def obj_create(self, bundle, **kwargs):
        """
        Handles creating Events through the API.

        :param bundle: Bundle containing the information to create the Event.
        :type bundle: Tastypie Bundle object.
        :returns: HttpResponse.
        :raises BadRequest: If a campaign name is not provided or creation fails.
        """

        analyst = bundle.request.user.username
        title = bundle.data.get('title', None)
        description = bundle.data.get('description', None)
        event_type = bundle.data.get('event_type', None)
        source = bundle.data.get('source', None)
        method = bundle.data.get('method', None)
        reference = bundle.data.get('reference', None)
        date = bundle.data.get('date', None)
        bucket_list = bundle.data.get('bucket_list', None)
        ticket = bundle.data.get('ticket', None)

        if not title and not event_type and not source:
            raise BadRequest('Must provide a title, event_type, and source.')
        et = EventType.objects(name=event_type).first()
        if not et:
            raise BadRequest('Not a valid Event Type.')

        result = add_new_event(title,
                               description,
                               event_type,
                               source,
                               method,
                               reference,
                               date,
                               analyst,
                               bucket_list,
                               ticket)

        content = {'return_code': 0,
                   'type': 'Event',
                   'message': result.get('message', ''),
                   'id': result.get('id', '')}
        if result.get('id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'events',
                                  'api_name': 'v1',
                                  'pk': result.get('id')})
            content['url'] = url
        if not result['success']:
            content['return_code'] = 1
        self.crits_response(content)
