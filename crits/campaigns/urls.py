from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^stats/$', views.campaign_stats),
    url(r'^name_list/$', views.campaign_names),
    url(r'^name_list/(?P<active_only>\S+)/$', views.campaign_names),
    url(r'^list/$', views.campaigns_listing),
    url(r'^list/(?P<option>\S+)/$', views.campaigns_listing),
    url(r'^details/(?P<campaign_name>.+?)/$', views.campaign_details),
    url(r'^add/(?P<ctype>\w+)/(?P<objectid>\w+)/$', views.campaign_add),
    url(r'^new/$', views.add_campaign),
    url(r'^remove/(?P<ctype>\w+)/(?P<objectid>\w+)/$', views.remove_campaign),
    url(r'^edit/(?P<ctype>\w+)/(?P<objectid>\w+)/$', views.edit_campaign),
    url(r'^ttp/(?P<cid>\w+)/$', views.campaign_ttp),
    url(r'^aliases/$', views.campaign_aliases),
]
