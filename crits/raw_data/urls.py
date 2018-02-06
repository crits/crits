from django.conf.urls import url

urlpatterns = [
    url(r'^details/(?P<_id>\w+)/$', 'raw_data_details', prefix='crits.raw_data.views'),
    url(r'^details_by_link/(?P<link>.+)/$', 'details_by_link', prefix='crits.raw_data.views'),
    url(r'^get_inline_comments/(?P<_id>\w+)/$', 'get_inline_comments', prefix='crits.raw_data.views'),
    url(r'^get_versions/(?P<_id>\w+)/$', 'get_raw_data_versions', prefix='crits.raw_data.views'),
    url(r'^set_tool_details/(?P<_id>\w+)/$', 'set_raw_data_tool_details', prefix='crits.raw_data.views'),
    url(r'^set_tool_name/(?P<_id>\w+)/$', 'set_raw_data_tool_name', prefix='crits.raw_data.views'),
    url(r'^set_raw_data_type/(?P<_id>\w+)/$', 'set_raw_data_type', prefix='crits.raw_data.views'),
    url(r'^set_raw_data_highlight_comment/(?P<_id>\w+)/$', 'set_raw_data_highlight_comment', prefix='crits.raw_data.views'),
    url(r'^set_raw_data_highlight_date/(?P<_id>\w+)/$', 'set_raw_data_highlight_date', prefix='crits.raw_data.views'),
    url(r'^add_inline_comment/(?P<_id>\w+)/$', 'add_inline_comment', prefix='crits.raw_data.views'),
    url(r'^add_highlight/(?P<_id>\w+)/$', 'add_highlight', prefix='crits.raw_data.views'),
    url(r'^remove_highlight/(?P<_id>\w+)/$', 'remove_highlight', prefix='crits.raw_data.views'),
    url(r'^upload/(?P<link_id>.+)/$', 'upload_raw_data', prefix='crits.raw_data.views'),
    url(r'^upload/$', 'upload_raw_data', prefix='crits.raw_data.views'),
    url(r'^remove/(?P<_id>[\S ]+)$', 'remove_raw_data', prefix='crits.raw_data.views'),
    url(r'^list/$', 'raw_data_listing', prefix='crits.raw_data.views'),
    url(r'^list/(?P<option>\S+)/$', 'raw_data_listing', prefix='crits.raw_data.views'),
    url(r'^add_data_type/$', 'new_raw_data_type', prefix='crits.raw_data.views'),
    url(r'^get_data_types/$', 'get_raw_data_type_dropdown', prefix='crits.raw_data.views'),
]
