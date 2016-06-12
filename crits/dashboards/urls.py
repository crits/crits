from django.conf.urls import url

# Dashboard
urlpatterns = [
    url(r'^new_saved_search/$', 'new_save_search', prefix='crits.dashboards.views'),
    url(r'^$', 'dashboard', prefix='crits.dashboards.views'),
    url(r'^id/(?P<dashId>\w+)/$', 'dashboard', prefix='crits.dashboards.views'),
    url(r'^edit_saved_search/(?P<id>\S+)/$', 'edit_save_search', prefix='crits.dashboards.views'),
    url(r'^delete_save_search/$', 'delete_save_search', prefix='crits.dashboards.views'),
    url(r'^load_data/(?P<obj>\w+)/$', 'load_data', prefix='crits.dashboards.views'),
    url(r'^load_data/(?P<obj>\w+)/(?P<term>\w+)/$', 'load_data', prefix='crits.dashboards.views'),
    url(r'^save_search/$', 'save_search', prefix='crits.dashboards.views'),
    url(r'^save_new_dashboard/$', 'save_new_dashboard', prefix='crits.dashboards.views'),
    url(r'^destroy_dashboard/$', 'destroy_dashboard', prefix='crits.dashboards.views'),
    url(r'^get_dashboard_table_data/(?P<tableName>\w+)/$', 'get_dashboard_table_data', prefix='crits.dashboards.views'),
    url(r'^configurations/$', 'saved_searches_list', prefix='crits.dashboards.views'),
    url(r'^toggle_table_visibility/$', 'toggle_table_visibility', prefix='crits.dashboards.views'),
    url(r'^set_default_dashboard/$', 'set_default_dashboard', prefix='crits.dashboards.views'),
    url(r'^set_dashboard_public/$', 'set_dashboard_public', prefix='crits.dashboards.views'),
    url(r'^ignore_parent/(?P<id>\S+)/$', 'ignore_parent', prefix='crits.dashboards.views'),
    url(r'^delete_dashboard/$', 'delete_dashboard', prefix='crits.dashboards.views'),
    url(r'^rename_dashboard/$', 'rename_dashboard', prefix='crits.dashboards.views'),
    url(r'^change_theme/$', 'change_theme', prefix='crits.dashboards.views'),
    url(r'^create_blank_dashboard/$', 'create_blank_dashboard', prefix='crits.dashboards.views'),
    url(r'^add_search/$', 'add_search', prefix='crits.dashboards.views'),
    url(r'^switch_dashboard/$', 'switch_dashboard', prefix='crits.dashboards.views'),
]
