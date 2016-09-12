from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^stats/$', views.campaign_stats, name='crits-campaigns-views-campaign_stats'),
    url(r'^name_list/$', views.campaign_names, name='crits-campaigns-views-campaign_names'),
    url(r'^name_list/(?P<active_only>\S+)/$', views.campaign_names, name='crits-campaigns-views-campaign_names'),
    url(r'^list/$', views.campaigns_listing, name='crits-campaigns-views-campaigns_listing'),
    url(r'^list/(?P<option>\S+)/$', views.campaigns_listing, name='crits-campaigns-views-campaigns_listing'),
    url(r'^details/(?P<campaign_name>.+?)/$', views.campaign_details, name='crits-campaigns-views-campaign_details'),
    url(r'^add/(?P<ctype>\w+)/(?P<objectid>\w+)/$', views.campaign_add, name='crits-campaigns-views-campaign_add'),
    url(r'^new/$', views.add_campaign, name='crits-campaigns-views-add_campaign'),
    url(r'^remove/(?P<ctype>\w+)/(?P<objectid>\w+)/$', views.remove_campaign, name='crits-campaigns-views-remove_campaign'),
    url(r'^edit/(?P<ctype>\w+)/(?P<objectid>\w+)/$', views.edit_campaign, name='crits-campaigns-views-edit_campaign'),
    url(r'^ttp/(?P<cid>\w+)/$', views.campaign_ttp, name='crits-campaigns-views-campaign_ttp'),
    url(r'^aliases/$', views.campaign_aliases, name='crits-campaigns-views-campaign_aliases'),
]
