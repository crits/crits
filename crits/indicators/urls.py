from django.conf.urls import url

urlpatterns = [
    url(r'^details/(?P<indicator_id>\w+)/$', 'indicator', prefix='crits.indicators.views'),
    url(r'^search/$', 'indicator_search', prefix='crits.indicators.views'),
    url(r'^upload/$', 'upload_indicator', prefix='crits.indicators.views'),
    url(r'^remove/(?P<_id>[\S ]+)$', 'remove_indicator', prefix='crits.indicators.views'),
    url(r'^activity/remove/(?P<indicator_id>\w+)/$', 'remove_activity', prefix='crits.indicators.views'),
    url(r'^activity/(?P<method>\S+)/(?P<indicator_id>\w+)/$', 'add_update_activity', prefix='crits.indicators.views'),
    url(r'^ci/update/(?P<indicator_id>\w+)/(?P<ci_type>\S+)/$', 'update_ci', prefix='crits.indicators.views'),
    url(r'^type/update/(?P<indicator_id>\w+)/$', 'update_indicator_type', prefix='crits.indicators.views'),
    url(r'^threat_type/update/(?P<indicator_id>\w+)/$', 'threat_type_modify', prefix='crits.indicators.views'),
    url(r'^attack_type/update/(?P<indicator_id>\w+)/$', 'attack_type_modify', prefix='crits.indicators.views'),
    url(r'^and_ip/$', 'indicator_and_ip', prefix='crits.indicators.views'),
    url(r'^from_obj/$', 'indicator_from_tlo', prefix='crits.indicators.views'),
    url(r'^list/$', 'indicators_listing', prefix='crits.indicators.views'),
    url(r'^list/(?P<option>\S+)/$', 'indicators_listing', prefix='crits.indicators.views'),
    url(r'^get_dropdown/$', 'get_indicator_type_dropdown', prefix='crits.indicators.views'),
    url(r'^get_threat_types/$', 'get_available_threat_types', prefix='crits.indicators.views'),
    url(r'^get_attack_types/$', 'get_available_attack_types', prefix='crits.indicators.views'),
]
