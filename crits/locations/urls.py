from django.conf.urls import patterns

urlpatterns = patterns('crits.locations.views',
    (r'^add/(?P<type_>\w+)/(?P<id_>\w+)/$', 'add_location'),
    (r'^edit/(?P<type_>\w+)/(?P<id_>\w+)/$', 'edit_location'),
    (r'^remove/(?P<type_>\w+)/(?P<id_>\w+)/$', 'remove_location'),
    (r'^name_list/$', 'location_names'),
    (r'^name_list/(?P<active_only>\S+)/$', 'location_names'),
)
