from django.conf.urls import url

urlpatterns = [
    url(r'^details/(?P<eventid>\w+)/$', 'view_event', prefix='crits.events.views'),
    url(r'^add/$', 'add_event', prefix='crits.events.views'),
    url(r'^search/$', 'event_search', prefix='crits.events.views'),
    url(r'^remove/(?P<_id>[\S ]+)$', 'remove_event', prefix='crits.events.views'),
    url(r'^set_title/(?P<event_id>\w+)/$', 'set_event_title', prefix='crits.events.views'),
    url(r'^set_type/(?P<event_id>\w+)/$', 'set_event_type', prefix='crits.events.views'),
    url(r'^get_event_types/$', 'get_event_type_dropdown', prefix='crits.events.views'),
    url(r'^list/$', 'events_listing', prefix='crits.events.views'),
    url(r'^list/(?P<option>\S+)/$', 'events_listing', prefix='crits.events.views'),
]
