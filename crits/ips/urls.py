from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^search/$', views.ip_search, name='crits-ips-views-ip_search'),
    url(r'^search/(?P<ip_str>\S+)/$', views.ip_search, name='crits-ips-views-ip_search'),
    url(r'^details/(?P<ip>\S+)/$', views.ip_detail, name='crits-ips-views-ip_detail'),
    url(r'^remove/$', views.remove_ip, name='crits-ips-views-remove_ip'),
    url(r'^list/$', views.ips_listing, name='crits-ips-views-ips_listing'),
    url(r'^list/(?P<option>\S+)/$', views.ips_listing, name='crits-ips-views-ips_listing'),
    url(r'^bulkadd/$', views.bulk_add_ip, name='crits-ips-views-bulk_add_ip'),
    url(r'^(?P<method>\S+)/$', views.add_update_ip, name='crits-ips-views-add_update_ip'),
]
