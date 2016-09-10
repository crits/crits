from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^details/(?P<_id>\w+)/$', views.raw_data_details),
    url(r'^details_by_link/(?P<link>.+)/$', views.details_by_link),
    url(r'^get_inline_comments/(?P<_id>\w+)/$', views.get_inline_comments),
    url(r'^get_versions/(?P<_id>\w+)/$', views.get_raw_data_versions),
    url(r'^set_tool_details/(?P<_id>\w+)/$', views.set_raw_data_tool_details),
    url(r'^set_tool_name/(?P<_id>\w+)/$', views.set_raw_data_tool_name),
    url(r'^set_raw_data_type/(?P<_id>\w+)/$', views.set_raw_data_type),
    url(r'^set_raw_data_highlight_comment/(?P<_id>\w+)/$', views.set_raw_data_highlight_comment),
    url(r'^set_raw_data_highlight_date/(?P<_id>\w+)/$', views.set_raw_data_highlight_date),
    url(r'^add_inline_comment/(?P<_id>\w+)/$', views.add_inline_comment),
    url(r'^add_highlight/(?P<_id>\w+)/$', views.add_highlight),
    url(r'^remove_highlight/(?P<_id>\w+)/$', views.remove_highlight),
    url(r'^upload/(?P<link_id>.+)/$', views.upload_raw_data),
    url(r'^upload/$', views.upload_raw_data),
    url(r'^remove/(?P<_id>[\S ]+)$', views.remove_raw_data),
    url(r'^list/$', views.raw_data_listing),
    url(r'^list/(?P<option>\S+)/$', views.raw_data_listing),
    url(r'^add_data_type/$', views.new_raw_data_type),
    url(r'^get_data_types/$', views.get_raw_data_type_dropdown),
]
