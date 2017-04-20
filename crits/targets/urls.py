from django.conf.urls import url

urlpatterns = [
    url(r'^list/$', 'targets_listing', prefix='crits.targets.views'),
    url(r'^list/(?P<option>\S+)/$', 'targets_listing', prefix='crits.targets.views'),
    url(r'^divisions/list/$', 'divisions_listing', prefix='crits.targets.views'),
    url(r'^divisions/list/(?P<option>\S+)/$', 'divisions_listing', prefix='crits.targets.views'),
    url(r'^add_target/$', 'add_update_target', prefix='crits.targets.views'),
    url(r'^details/(?P<email_address>[\S ]+)/$', 'target_details', prefix='crits.targets.views'),
    url(r'^details/$', 'target_details', prefix='crits.targets.views'),
    url(r'^info/(?P<email_address>[\S ]+)/$', 'target_info', prefix='crits.targets.views'),
]
