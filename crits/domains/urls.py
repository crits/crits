from django.conf.urls import patterns

urlpatterns = patterns('crits.domains.views',
    (r'^list/$', 'domains_listing'),
    (r'^list/(?P<option>\S+)/$', 'domains_listing'),
    (r'^tld_update/$', 'tld_update'),
    (r'^details/(?P<domain>\S+)/$', 'domain_detail'),
    (r'^search/$', 'domain_search'),
    (r'^add/$', 'add_domain'),
    (r'^bulkadd/$', 'bulk_add_domain'),
    (r'^edit/(?P<domain>\S+)/$', 'edit_domain'),
)
