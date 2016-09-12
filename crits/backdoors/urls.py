from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^add/$', views.add_backdoor, name='crits-backdoors-views-add_backdoor'),
    url(r'^edit/aliases/$', views.edit_backdoor_aliases, name='crits-backdoors-views-edit_backdoor_aliases'),
    url(r'^edit/name/(?P<id_>\S+)/$', views.edit_backdoor_name, name='crits-backdoors-views-edit_backdoor_name'),
    url(r'^edit/version/(?P<id_>\S+)/$', views.edit_backdoor_version, name='crits-backdoors-views-edit_backdoor_version'),
    url(r'^details/(?P<id_>\S+)/$', views.backdoor_detail, name='crits-backdoors-views-backdoor_detail'),
    url(r'^remove/(?P<id_>\S+)/$', views.remove_backdoor, name='crits-backdoors-views-remove_backdoor'),
    url(r'^list/$', views.backdoors_listing, name='crits-backdoors-views-backdoors_listing'),
    url(r'^list/(?P<option>\S+)/$', views.backdoors_listing, name='crits-backdoors-views-backdoors_listing'),
]
