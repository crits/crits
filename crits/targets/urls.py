from django.conf.urls import patterns

urlpatterns = patterns('crits.targets.views',
    (r'^list/$', 'targets_listing'),
    (r'^list/(?P<option>\S+)/$', 'targets_listing'),
    (r'^divisions/list/$', 'divisions_listing'),
    (r'^divisions/list/(?P<option>\S+)/$', 'divisions_listing'),
    (r'^add_target/$', 'add_update_target'),
    (r'^details/(?P<email_address>[\S ]+)/$', 'target_details'),
    (r'^details/$', 'target_details'),
    (r'^info/(?P<email_address>[\S ]+)/$', 'target_info'),
)
