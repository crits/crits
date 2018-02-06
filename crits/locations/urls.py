from django.conf.urls import url

urlpatterns = [
    url(r'^add/(?P<type_>\w+)/(?P<id_>\w+)/$', 'add_location', prefix='crits.locations.views'),
    url(r'^edit/(?P<type_>\w+)/(?P<id_>\w+)/$', 'edit_location', prefix='crits.locations.views'),
    url(r'^remove/(?P<type_>\w+)/(?P<id_>\w+)/$', 'remove_location', prefix='crits.locations.views'),
    url(r'^name_list/$', 'location_names', prefix='crits.locations.views'),
    url(r'^name_list/(?P<active_only>\S+)/$', 'location_names', prefix='crits.locations.views'),
]
