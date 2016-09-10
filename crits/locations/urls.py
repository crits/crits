from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^add/(?P<type_>\w+)/(?P<id_>\w+)/$', views.add_location),
    url(r'^edit/(?P<type_>\w+)/(?P<id_>\w+)/$', views.edit_location),
    url(r'^remove/(?P<type_>\w+)/(?P<id_>\w+)/$', views.remove_location),
    url(r'^name_list/$', views.location_names),
    url(r'^name_list/(?P<active_only>\S+)/$', views.location_names),
]
