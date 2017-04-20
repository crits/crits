from django.conf.urls import url

urlpatterns = [
    url(r'^search/$', 'email_search', prefix='crits.emails.views'),
    url(r'^delete/(?P<email_id>\w+)/$', 'email_del', prefix='crits.emails.views'),
    url(r'^upload/attach/(?P<email_id>\w+)/$', 'upload_attach', prefix='crits.emails.views'),
    url(r'^details/(?P<email_id>\w+)/$', 'email_detail', prefix='crits.emails.views'),
    url(r'^new/fields/$', 'email_fields_add', prefix='crits.emails.views'),
    url(r'^new/outlook/$', 'email_outlook_add', prefix='crits.emails.views'),
    url(r'^new/raw/$', 'email_raw_add', prefix='crits.emails.views'),
    url(r'^new/yaml/$', 'email_yaml_add', prefix='crits.emails.views'),
    url(r'^new/eml/$', 'email_eml_add', prefix='crits.emails.views'),
    url(r'^edit/(?P<email_id>\w+)/$', 'email_yaml_add', prefix='crits.emails.views'),
    url(r'^update_header_value/(?P<email_id>\w+)/$', 'update_header_value', prefix='crits.emails.views'),
    url(r'^indicator_from_header_field/(?P<email_id>\w+)/$', 'indicator_from_header_field', prefix='crits.emails.views'),
    url(r'^list/$', 'emails_listing', prefix='crits.emails.views'),
    url(r'^list/(?P<option>\S+)/$', 'emails_listing', prefix='crits.emails.views'),
]
