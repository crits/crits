from django.conf.urls import url

urlpatterns = [
    url(r'^stats/$', 'campaign_stats', prefix='crits.campaigns.views'),
    url(r'^name_list/$', 'campaign_names', prefix='crits.campaigns.views'),
    url(r'^name_list/(?P<active_only>\S+)/$', 'campaign_names', prefix='crits.campaigns.views'),
    url(r'^list/$', 'campaigns_listing', prefix='crits.campaigns.views'),
    url(r'^list/(?P<option>\S+)/$', 'campaigns_listing', prefix='crits.campaigns.views'),
    url(r'^details/(?P<campaign_name>.+?)/$', 'campaign_details', prefix='crits.campaigns.views'),
    url(r'^add/(?P<ctype>\w+)/(?P<objectid>\w+)/$', 'campaign_add', prefix='crits.campaigns.views'),
    url(r'^new/$', 'add_campaign', prefix='crits.campaigns.views'),
    url(r'^remove/(?P<ctype>\w+)/(?P<objectid>\w+)/$', 'remove_campaign', prefix='crits.campaigns.views'),
    url(r'^edit/(?P<ctype>\w+)/(?P<objectid>\w+)/$', 'edit_campaign', prefix='crits.campaigns.views'),
    url(r'^ttp/(?P<cid>\w+)/$', 'campaign_ttp', prefix='crits.campaigns.views'),
    url(r'^aliases/$', 'campaign_aliases', prefix='crits.campaigns.views'),
]
