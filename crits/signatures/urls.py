from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^details/(?P<_id>\w+)/$', views.signature_detail),
    url(r'^details_by_link/(?P<link>.+)/$', views.details_by_link),
    url(r'^get_versions/(?P<_id>\w+)/$', views.get_signature_versions),
    url(r'^set_signature_type/(?P<id_>\w+)/$', views.set_signature_type),
    url(r'^update_data_type_min_version/$', views.update_data_type_min_version),
    url(r'^update_data_type_max_version/$', views.update_data_type_max_version),
    url(r'^update_data_type_dependency/$', views.update_data_type_dependency),
    url(r'^upload/(?P<link_id>.+)/$', views.upload_signature),
    url(r'^upload/$', views.upload_signature),
    url(r'^remove/(?P<_id>[\S ]+)$', views.remove_signature),
    url(r'^list/$', views.signatures_listing),
    url(r'^list/(?P<option>\S+)/$', views.signatures_listing),
    url(r'^add_data_type/$', views.new_signature_type),
    url(r'^add_data_dependency/$', views.new_signature_dependency),
    url(r'^get_data_types/$', views.get_signature_type_dropdown),
    url(r'^signatures/autocomplete/$', views.dependency_autocomplete),
    url(r'^remove_signature_dependency/$', views.remove_signature_dependency),
]
