from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^details/(?P<md5>\w+)/$', views.pcap_details, name='crits-pcaps-views-pcap_details'),
    url(r'^upload/$', views.upload_pcap, name='crits-pcaps-views-upload_pcap'),
    url(r'^remove/(?P<md5>[\S ]+)$', views.remove_pcap, name='crits-pcaps-views-remove_pcap'),
    url(r'^list/$', views.pcaps_listing, name='crits-pcaps-views-pcaps_listing'),
    url(r'^list/(?P<option>\S+)/$', views.pcaps_listing, name='crits-pcaps-views-pcaps_listing'),
]
