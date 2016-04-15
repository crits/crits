from django.conf.urls import patterns

urlpatterns = patterns('crits.ips.views',
    (r'^search/$', 'ip_search'),
    (r'^search/(?P<ip_str>\S+)/$', 'ip_search'),
    (r'^details/(?P<ip>\S+)/$', 'ip_detail'),
    (r'^remove/$', 'remove_ip'),
    (r'^list/$', 'ips_listing'),
    (r'^list/(?P<option>\S+)/$', 'ips_listing'),
    (r'^bulkadd/$', 'bulk_add_ip'),
    (r'^(?P<method>\S+)/$', 'add_update_ip'),
)
