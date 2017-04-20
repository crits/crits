from django.conf.urls import url

urlpatterns = [
    url(r'^details/(?P<md5>\w+)/$', 'pcap_details', prefix='crits.pcaps.views'),
    url(r'^upload/$', 'upload_pcap', prefix='crits.pcaps.views'),
    url(r'^remove/(?P<md5>[\S ]+)$', 'remove_pcap', prefix='crits.pcaps.views'),
    url(r'^list/$', 'pcaps_listing', prefix='crits.pcaps.views'),
    url(r'^list/(?P<option>\S+)/$', 'pcaps_listing', prefix='crits.pcaps.views'),
]
