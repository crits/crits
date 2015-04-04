from django.conf.urls import patterns

urlpatterns = patterns('crits.campaigns.views',
    (r'^stats/$', 'campaign_stats'),
    (r'^name_list/$', 'campaign_names'),
    (r'^name_list/(?P<active_only>\S+)/$', 'campaign_names'),
    (r'^list/$', 'campaigns_listing'),
    (r'^list/(?P<option>\S+)/$', 'campaigns_listing'),
    (r'^details/(?P<campaign_name>.+?)/$', 'campaign_details'),
    (r'^add/(?P<ctype>\w+)/(?P<objectid>\w+)/$', 'campaign_add'),
    (r'^new/$', 'add_campaign'),
    (r'^remove/(?P<ctype>\w+)/(?P<objectid>\w+)/$', 'remove_campaign'),
    (r'^edit/(?P<ctype>\w+)/(?P<objectid>\w+)/$', 'edit_campaign'),
    (r'^ttp/(?P<cid>\w+)/$', 'campaign_ttp'),
    (r'^aliases/$', 'campaign_aliases'),
)
