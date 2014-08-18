from django.conf.urls import patterns

urlpatterns = patterns('',
    # Dashboard
    (r'^new_save_search/$', 'crits.core.dashboard.views.new_save_search'),
    (r'^dashboard/(?P<dashId>\w+)/$', 'crits.core.dashboard.views.dashboard'),
    (r'^edit_save_search/(?P<id>\S+)/$', 'crits.core.dashboard.views.edit_save_search'),
    (r'^delete_save_search/$', 'crits.core.dashboard.views.delete_save_search'),
    (r'^load_data/(?P<obj>\w+)/$', 'crits.core.dashboard.views.load_data'),
    (r'^load_data/(?P<obj>\w+)/(?P<term>\w+)/$', 'crits.core.dashboard.views.load_data'),
    (r'^save_search/$', 'crits.core.dashboard.views.save_search'),
    (r'^save_new_dashboard/$', 'crits.core.dashboard.views.save_new_dashboard'),
    (r'^destroy_dashboard/$', 'crits.core.dashboard.views.destroy_dashboard'),
    (r'^get_dashboard_table_data/(?P<tableName>\w+)/$', 'crits.core.dashboard.views.get_dashboard_table_data'),
    (r'^saved_searches_list/$', 'crits.core.dashboard.views.saved_searches_list'),
    (r'^toggle_table_visibility/$', 'crits.core.dashboard.views.toggle_table_visibility'),
    (r'^set_default_dashboard/$', 'crits.core.dashboard.views.set_default_dashboard'),
    (r'^set_dashboard_public/$', 'crits.core.dashboard.views.set_dashboard_public'),
    (r'^ignore_parent/(?P<id>\S+)/$', 'crits.core.dashboard.views.ignore_parent'),
    (r'^delete_dashboard/$', 'crits.core.dashboard.views.delete_dashboard'),
    (r'^rename_dashboard/$', 'crits.core.dashboard.views.rename_dashboard'),
    (r'^change_theme/$', 'crits.core.dashboard.views.change_theme'),
)
