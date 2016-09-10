from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^list/$', views.domains_listing),
    url(r'^list/(?P<option>\S+)/$', views.domains_listing),
    url(r'^tld_update/$', views.tld_update),
    url(r'^details/(?P<domain>\S+)/$', views.domain_detail),
    url(r'^search/$', views.domain_search),
    url(r'^add/$', views.add_domain),
    url(r'^bulkadd/$', views.bulk_add_domain),
    url(r'^edit/(?P<domain>\S+)/$', views.edit_domain),
]
