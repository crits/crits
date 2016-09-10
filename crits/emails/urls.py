from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^search/$', views.email_search),
    url(r'^delete/(?P<email_id>\w+)/$', views.email_del),
    url(r'^upload/attach/(?P<email_id>\w+)/$', views.upload_attach),
    url(r'^details/(?P<email_id>\w+)/$', views.email_detail),
    url(r'^new/fields/$', views.email_fields_add),
    url(r'^new/outlook/$', views.email_outlook_add),
    url(r'^new/raw/$', views.email_raw_add),
    url(r'^new/yaml/$', views.email_yaml_add),
    url(r'^new/eml/$', views.email_eml_add),
    url(r'^edit/(?P<email_id>\w+)/$', views.email_yaml_add),
    url(r'^update_header_value/(?P<email_id>\w+)/$', views.update_header_value),
    url(r'^indicator_from_header_field/(?P<email_id>\w+)/$', views.indicator_from_header_field),
    url(r'^list/$', views.emails_listing),
    url(r'^list/(?P<option>\S+)/$', views.emails_listing),
]
