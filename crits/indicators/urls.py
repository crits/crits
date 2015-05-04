from django.conf.urls import patterns

urlpatterns = patterns('crits.indicators.views',
    (r'^details/(?P<indicator_id>\w+)/$', 'indicator'),
    (r'^search/$', 'indicator_search'),
    (r'^upload/$', 'upload_indicator'),
    (r'^add_action/$', 'new_indicator_action'),
    (r'^remove/(?P<_id>[\S ]+)$', 'remove_indicator'),
    (r'^action/remove/(?P<indicator_id>\w+)/$', 'remove_action'),
    (r'^activity/remove/(?P<indicator_id>\w+)/$', 'remove_activity'),
    (r'^actions/(?P<method>\S+)/(?P<indicator_id>\w+)/$', 'add_update_action'),
    (r'^activity/(?P<method>\S+)/(?P<indicator_id>\w+)/$', 'add_update_activity'),
    (r'^ci/update/(?P<indicator_id>\w+)/(?P<ci_type>\S+)/$', 'update_ci'),
    (r'^type/update/(?P<indicator_id>\w+)/$', 'update_indicator_type'),
    (r'^and_ip/$', 'indicator_and_ip'),
    (r'^from_obj/$', 'indicator_from_tlo'),
    (r'^list/$', 'indicators_listing'),
    (r'^list/(?P<option>\S+)/$', 'indicators_listing'),
)
