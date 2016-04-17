from __future__ import unicode_literals
from django.conf.urls import patterns

urlpatterns = patterns('crits.signatures.views',
    (r'^details/(?P<_id>\w+)/$', 'signature_detail'),
    (r'^details_by_link/(?P<link>.+)/$', 'details_by_link'),
    (r'^get_versions/(?P<_id>\w+)/$', 'get_signature_versions'),
    (r'^set_signature_type/(?P<id_>\w+)/$', 'set_signature_type'),
    (r'^update_data_type_min_version/$', 'update_data_type_min_version'),
    (r'^update_data_type_max_version/$', 'update_data_type_max_version'),
    (r'^update_data_type_dependency/$', 'update_data_type_dependency'),
    (r'^upload/(?P<link_id>.+)/$', 'upload_signature'),
    (r'^upload/$', 'upload_signature'),
    (r'^remove/(?P<_id>[\S ]+)$', 'remove_signature'),
    (r'^list/$', 'signatures_listing'),
    (r'^list/(?P<option>\S+)/$', 'signatures_listing'),
    (r'^add_data_type/$', 'new_signature_type'),
    (r'^add_data_dependency/$', 'new_signature_dependency'),
    (r'^get_data_types/$', 'get_signature_type_dropdown'),
    (r'^signatures/autocomplete/$', 'dependency_autocomplete'),
    (r'^remove_signature_dependency/$', 'remove_signature_dependency'),
)
