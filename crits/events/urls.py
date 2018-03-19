from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^details/(?P<eventid>\w+)/$', views.view_event, name='crits-events-views-view_event'),
    url(r'^add/$', views.add_event, name='crits-events-views-add_event'),
    url(r'^search/$', views.event_search, name='crits-events-views-event_search'),
    url(r'^remove/(?P<_id>[\S ]+)$', views.remove_event, name='crits-events-views-remove_event'),
    url(r'^set_title/(?P<event_id>\w+)/$', views.set_event_title, name='crits-events-views-set_event_title'),
    url(r'^set_type/(?P<event_id>\w+)/$', views.set_event_type, name='crits-events-views-set_event_type'),
    url(r'^get_event_types/$', views.get_event_type_dropdown, name='crits-events-views-get_event_type_dropdown'),
    url(r'^list/$', views.events_listing, name='crits-events-views-events_listing'),
    url(r'^list/(?P<option>\S+)/$', views.events_listing, name='crits-events-views-events_listing'),
]
