from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^details/(?P<indicator_id>\w+)/$', views.indicator, name='crits-indicators-views-indicator'),
    url(r'^search/$', views.indicator_search, name='crits-indicators-views-indicator_search'),
    url(r'^upload/$', views.upload_indicator, name='crits-indicators-views-upload_indicator'),
    url(r'^remove/(?P<_id>[\S ]+)$', views.remove_indicator, name='crits-indicators-views-remove_indicator'),
    url(r'^activity/remove/(?P<indicator_id>\w+)/$', views.remove_activity, name='crits-indicators-views-remove_activity'),
    url(r'^activity/(?P<method>\S+)/(?P<indicator_id>\w+)/$', views.add_update_activity, name='crits-indicators-views-add_update_activity'),
    url(r'^ci/update/(?P<indicator_id>\w+)/(?P<ci_type>\S+)/$', views.update_ci, name='crits-indicators-views-update_ci'),
    url(r'^type/update/(?P<indicator_id>\w+)/$', views.update_indicator_type, name='crits-indicators-views-update_indicator_type'),
    url(r'^threat_type/update/(?P<indicator_id>\w+)/$', views.threat_type_modify, name='crits-indicators-views-threat_type_modify'),
    url(r'^attack_type/update/(?P<indicator_id>\w+)/$', views.attack_type_modify, name='crits-indicators-views-attack_type_modify'),
    url(r'^and_ip/$', views.indicator_and_ip, name='crits-indicators-views-indicator_and_ip'),
    url(r'^from_obj/$', views.indicator_from_tlo, name='crits-indicators-views-indicator_from_tlo'),
    url(r'^list/$', views.indicators_listing, name='crits-indicators-views-indicators_listing'),
    url(r'^list/(?P<option>\S+)/$', views.indicators_listing, name='crits-indicators-views-indicators_listing'),
    url(r'^get_dropdown/$', views.get_indicator_type_dropdown, name='crits-indicators-views-get_indicator_type_dropdown'),
    url(r'^get_threat_types/$', views.get_available_threat_types, name='crits-indicators-views-get_available_threat_types'),
    url(r'^get_attack_types/$', views.get_available_attack_types, name='crits-indicators-views-get_available_attack_types'),
]
