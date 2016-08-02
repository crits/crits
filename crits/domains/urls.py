from django.conf.urls import url

urlpatterns = [
    url(r'^list/$', 'domains_listing', prefix='crits.domains.views'),
    url(r'^list/(?P<option>\S+)/$', 'domains_listing', prefix='crits.domains.views'),
    url(r'^tld_update/$', 'tld_update', prefix='crits.domains.views'),
    url(r'^details/(?P<domain>\S+)/$', 'domain_detail', prefix='crits.domains.views'),
    url(r'^search/$', 'domain_search', prefix='crits.domains.views'),
    url(r'^add/$', 'add_domain', prefix='crits.domains.views'),
    url(r'^bulkadd/$', 'bulk_add_domain', prefix='crits.domains.views'),
    url(r'^edit/(?P<domain>\S+)/$', 'edit_domain', prefix='crits.domains.views'),
]
