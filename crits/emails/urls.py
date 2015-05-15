from django.conf.urls import patterns

urlpatterns = patterns('crits.emails.views',
    (r'^search/$', 'email_search'),
    (r'^delete/(?P<email_id>\w+)/$', 'email_del'),
    (r'^upload/attach/(?P<email_id>\w+)/$', 'upload_attach'),
    (r'^details/(?P<email_id>\w+)/$', 'email_detail'),
    (r'^new/fields/$', 'email_fields_add'),
    (r'^new/outlook/$', 'email_outlook_add'),
    (r'^new/raw/$', 'email_raw_add'),
    (r'^new/yaml/$', 'email_yaml_add'),
    (r'^new/eml/$', 'email_eml_add'),
    (r'^edit/(?P<email_id>\w+)/$', 'email_yaml_add'),
    (r'^update_header_value/(?P<email_id>\w+)/$', 'update_header_value'),
    (r'^indicator_from_header_field/(?P<email_id>\w+)/$', 'indicator_from_header_field'),
    (r'^list/$', 'emails_listing'),
    (r'^list/(?P<option>\S+)/$', 'emails_listing'),
)
