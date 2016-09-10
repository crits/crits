from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^list/$', views.targets_listing),
    url(r'^list/(?P<option>\S+)/$', views.targets_listing),
    url(r'^divisions/list/$', views.divisions_listing),
    url(r'^divisions/list/(?P<option>\S+)/$', views.divisions_listing),
    url(r'^add_target/$', views.add_update_target),
    url(r'^details/(?P<email_address>[\S ]+)/$', views.target_details),
    url(r'^details/$', views.target_details),
    url(r'^info/(?P<email_address>[\S ]+)/$', views.target_info),
]
