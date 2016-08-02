from django.conf.urls import url

urlpatterns = [
    url(r'^add/$', 'add_backdoor', prefix='crits.backdoors.views'),
    url(r'^edit/aliases/$', 'edit_backdoor_aliases', prefix='crits.backdoors.views'),
    url(r'^edit/name/(?P<id_>\S+)/$', 'edit_backdoor_name', prefix='crits.backdoors.views'),
    url(r'^edit/version/(?P<id_>\S+)/$', 'edit_backdoor_version', prefix='crits.backdoors.views'),
    url(r'^details/(?P<id_>\S+)/$', 'backdoor_detail', prefix='crits.backdoors.views'),
    url(r'^remove/(?P<id_>\S+)/$', 'remove_backdoor', prefix='crits.backdoors.views'),
    url(r'^list/$', 'backdoors_listing', prefix='crits.backdoors.views'),
    url(r'^list/(?P<option>\S+)/$', 'backdoors_listing', prefix='crits.backdoors.views'),
]
