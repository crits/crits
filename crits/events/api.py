try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from tastypie import authorization
from tastypie.authentication import MultiAuthentication

from crits.events.event import Event
from crits.events.handlers import add_new_event
from crits.core.api import CRITsApiKeyAuthentication, CRITsSessionAuthentication
from crits.core.api import CRITsSerializer, CRITsAPIResource

from crits.vocabulary.events import EventTypes
from crits.vocabulary.acls import EventACL


class EventResource(CRITsAPIResource):
    """
    Class to handle everything related to the Event API.

    Currently supports GET and POST.
    """

    class Meta:
        object_class = Event
        allowed_methods = ('get', 'post', 'patch')
        resource_name = "events"
        ordering = ("title", "event_type", "created", "status", "id")
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
        """

        user  = bundle.request.user
        title = bundle.data.get('title', None)
        description = bundle.data.get('description', None)
        event_type = bundle.data.get('event_type', None)
        source = bundle.data.get('source', None)
        method = bundle.data.get('method', None)
        reference = bundle.data.get('reference', None)
        tlp = bundle.data.get('tlp', 'amber')
        date = bundle.data.get('date', None)
        bucket_list = bundle.data.get('bucket_list', None)
        ticket = bundle.data.get('ticket', None)
        campaign = bundle.data.get('campaign', None)
        campaign_confidence = bundle.data.get('campaign_confidence', None)

        content = {'return_code': 0,
                   'type': 'Event'}
        if not title or not event_type or not source or not description:
            content['message'] = 'Must provide a title, event_type, source, and description.'
            self.crits_response(content)
        if event_type not in EventTypes.values():
            content['message'] = 'Not a valid Event Type.'
            self.crits_response(content)

        if user.has_access_to(EventACL.WRITE):
            result = add_new_event(title,
                                   description,
                                   event_type,
                                   source,
                                   method,
                                   reference,
                                   tlp,
                                   date,
                                   user,
                                   bucket_list,
                                   ticket,
                                   campaign,
                                   campaign_confidence)
        else:
            result = {'success':False,
                      'message':'User does not have permission to create Object.'}

        if result.get('message'):
            content['message'] = result.get('message')
        content['id'] = result.get('id', '')
        if result.get('id'):
            url = reverse('api_dispatch_detail',
                          kwargs={'resource_name': 'events',
                                  'api_name': 'v1',
                                  'pk': result.get('id')})
            content['url'] = url
        if result['success']:
            content['return_code'] = 0
        else:
            content['return_code'] = 1
        self.crits_response(content)
