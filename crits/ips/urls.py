from django.conf.urls import url

urlpatterns = [
    url(r'^search/$', 'ip_search', prefix='crits.ips.views'),
    url(r'^search/(?P<ip_str>\S+)/$', 'ip_search', prefix='crits.ips.views'),
    url(r'^details/(?P<ip>\S+)/$', 'ip_detail', prefix='crits.ips.views'),
    url(r'^remove/$', 'remove_ip', prefix='crits.ips.views'),
    url(r'^list/$', 'ips_listing', prefix='crits.ips.views'),
    url(r'^list/(?P<option>\S+)/$', 'ips_listing', prefix='crits.ips.views'),
    url(r'^bulkadd/$', 'bulk_add_ip', prefix='crits.ips.views'),
    url(r'^(?P<method>\S+)/$', 'add_update_ip', prefix='crits.ips.views'),
]
