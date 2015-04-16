from django.conf.urls import patterns

urlpatterns = patterns('crits.events.views',
    (r'^details/(?P<eventid>\w+)/$', 'view_event'),
    (r'^add/$', 'add_event'),
    (r'^search/$', 'event_search'),
    (r'^upload/sample/(?P<event_id>\w+)/$', 'upload_sample'),
    (r'^remove/(?P<_id>[\S ]+)$', 'remove_event'),
    (r'^set_title/(?P<event_id>\w+)/$', 'set_event_title'),
    (r'^set_type/(?P<event_id>\w+)/$', 'set_event_type'),
    (r'^get_event_types/$', 'get_event_type_dropdown'),
    (r'^list/$', 'events_listing'),
    (r'^list/(?P<option>\S+)/$', 'events_listing'),
)
