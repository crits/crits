from django.conf.urls import url

urlpatterns = [
    url(r'^details/(?P<_id>\w+)/$', 'signature_detail', prefix='crits.signatures.views'),
    url(r'^details_by_link/(?P<link>.+)/$', 'details_by_link', prefix='crits.signatures.views'),
    url(r'^get_versions/(?P<_id>\w+)/$', 'get_signature_versions', prefix='crits.signatures.views'),
    url(r'^set_signature_type/(?P<id_>\w+)/$', 'set_signature_type', prefix='crits.signatures.views'),
    url(r'^update_data_type_min_version/$', 'update_data_type_min_version', prefix='crits.signatures.views'),
    url(r'^update_data_type_max_version/$', 'update_data_type_max_version', prefix='crits.signatures.views'),
    url(r'^update_data_type_dependency/$', 'update_data_type_dependency', prefix='crits.signatures.views'),
    url(r'^upload/(?P<link_id>.+)/$', 'upload_signature', prefix='crits.signatures.views'),
    url(r'^upload/$', 'upload_signature', prefix='crits.signatures.views'),
    url(r'^remove/(?P<_id>[\S ]+)$', 'remove_signature', prefix='crits.signatures.views'),
    url(r'^list/$', 'signatures_listing', prefix='crits.signatures.views'),
    url(r'^list/(?P<option>\S+)/$', 'signatures_listing', prefix='crits.signatures.views'),
    url(r'^add_data_type/$', 'new_signature_type', prefix='crits.signatures.views'),
    url(r'^add_data_dependency/$', 'new_signature_dependency', prefix='crits.signatures.views'),
    url(r'^get_data_types/$', 'get_signature_type_dropdown', prefix='crits.signatures.views'),
    url(r'^signatures/autocomplete/$', 'dependency_autocomplete', prefix='crits.signatures.views'),
    url(r'^remove_signature_dependency/$', 'remove_signature_dependency', prefix='crits.signatures.views'),
]
