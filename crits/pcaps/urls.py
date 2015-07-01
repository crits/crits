from django.conf.urls import patterns

urlpatterns = patterns('crits.pcaps.views',
    (r'^details/(?P<md5>\w+)/$', 'pcap_details'),
    (r'^upload/$', 'upload_pcap'),
    (r'^remove/(?P<md5>[\S ]+)$', 'remove_pcap'),
    (r'^list/$', 'pcaps_listing'),
    (r'^list/(?P<option>\S+)/$', 'pcaps_listing'),
)
