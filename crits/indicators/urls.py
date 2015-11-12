from django.conf.urls import patterns

urlpatterns = patterns('crits.indicators.views',
    (r'^details/(?P<indicator_id>\w+)/$', 'indicator'),
    (r'^search/$', 'indicator_search'),
    (r'^upload/$', 'upload_indicator'),
    (r'^remove/(?P<_id>[\S ]+)$', 'remove_indicator'),
    (r'^activity/remove/(?P<indicator_id>\w+)/$', 'remove_activity'),
    (r'^activity/(?P<method>\S+)/(?P<indicator_id>\w+)/$', 'add_update_activity'),
    (r'^ci/update/(?P<indicator_id>\w+)/(?P<ci_type>\S+)/$', 'update_ci'),
    (r'^type/update/(?P<indicator_id>\w+)/$', 'update_indicator_type'),
    (r'^threat_type/update/(?P<indicator_id>\w+)/$', 'update_indicator_threat_type'),
    (r'^attack_type/update/(?P<indicator_id>\w+)/$', 'update_indicator_attack_type'),
    (r'^and_ip/$', 'indicator_and_ip'),
    (r'^from_obj/$', 'indicator_from_tlo'),
    (r'^list/$', 'indicators_listing'),
    (r'^list/(?P<option>\S+)/$', 'indicators_listing'),
    (r'^get_dropdown/$', 'get_indicator_type_dropdown'),
)
