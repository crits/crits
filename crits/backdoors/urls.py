from django.conf.urls import patterns

urlpatterns = patterns('crits.backdoors.views',
    (r'^add/$', 'add_backdoor'),
    (r'^edit/aliases/$', 'edit_backdoor_aliases'),
    (r'^edit/name/(?P<id_>\S+)/$', 'edit_backdoor_name'),
    (r'^edit/version/(?P<id_>\S+)/$', 'edit_backdoor_version'),
    (r'^details/(?P<id_>\S+)/$', 'backdoor_detail'),
    (r'^remove/(?P<id_>\S+)/$', 'remove_backdoor'),
    (r'^list/$', 'backdoors_listing'),
    (r'^list/(?P<option>\S+)/$', 'backdoors_listing'),
)
