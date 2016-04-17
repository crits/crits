from __future__ import unicode_literals
from django.conf.urls import patterns

urlpatterns = patterns('crits.raw_data.views',
    (r'^details/(?P<_id>\w+)/$', 'raw_data_details'),
    (r'^details_by_link/(?P<link>.+)/$', 'details_by_link'),
    (r'^get_inline_comments/(?P<_id>\w+)/$', 'get_inline_comments'),
    (r'^get_versions/(?P<_id>\w+)/$', 'get_raw_data_versions'),
    (r'^set_tool_details/(?P<_id>\w+)/$', 'set_raw_data_tool_details'),
    (r'^set_tool_name/(?P<_id>\w+)/$', 'set_raw_data_tool_name'),
    (r'^set_raw_data_type/(?P<_id>\w+)/$', 'set_raw_data_type'),
    (r'^set_raw_data_highlight_comment/(?P<_id>\w+)/$', 'set_raw_data_highlight_comment'),
    (r'^set_raw_data_highlight_date/(?P<_id>\w+)/$', 'set_raw_data_highlight_date'),
    (r'^add_inline_comment/(?P<_id>\w+)/$', 'add_inline_comment'),
    (r'^add_highlight/(?P<_id>\w+)/$', 'add_highlight'),
    (r'^remove_highlight/(?P<_id>\w+)/$', 'remove_highlight'),
    (r'^upload/(?P<link_id>.+)/$', 'upload_raw_data'),
    (r'^upload/$', 'upload_raw_data'),
    (r'^remove/(?P<_id>[\S ]+)$', 'remove_raw_data'),
    (r'^list/$', 'raw_data_listing'),
    (r'^list/(?P<option>\S+)/$', 'raw_data_listing'),
    (r'^add_data_type/$', 'new_raw_data_type'),
    (r'^get_data_types/$', 'get_raw_data_type_dropdown'),
)
