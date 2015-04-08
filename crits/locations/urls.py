from django.conf.urls import patterns

urlpatterns = patterns('crits.locations.views',
    (r'^add/(?P<type_>\w+)/(?P<id_>\w+)/$', 'add_location'),
    (r'^remove/(?P<type_>\w+)/(?P<id_>\w+)/$', 'remove_location'),
)
