from django.conf.urls import url

from . import views

# Dashboard
urlpatterns = [
    url(r'^new_saved_search/$', views.new_save_search),
    url(r'^$', views.dashboard),
    url(r'^id/(?P<dashId>\w+)/$', views.dashboard),
    url(r'^edit_saved_search/(?P<id>\S+)/$', views.edit_save_search),
    url(r'^delete_save_search/$', views.delete_save_search),
    url(r'^load_data/(?P<obj>\w+)/$', views.load_data),
    url(r'^load_data/(?P<obj>\w+)/(?P<term>\w+)/$', views.load_data),
    url(r'^save_search/$', views.save_search),
    url(r'^save_new_dashboard/$', views.save_new_dashboard),
    url(r'^destroy_dashboard/$', views.destroy_dashboard),
    url(r'^get_dashboard_table_data/(?P<tableName>\w+)/$', views.get_dashboard_table_data),
    url(r'^configurations/$', views.saved_searches_list),
    url(r'^toggle_table_visibility/$', views.toggle_table_visibility),
    url(r'^set_default_dashboard/$', views.set_default_dashboard),
    url(r'^set_dashboard_public/$', views.set_dashboard_public),
    url(r'^ignore_parent/(?P<id>\S+)/$', views.ignore_parent),
    url(r'^delete_dashboard/$', views.delete_dashboard),
    url(r'^rename_dashboard/$', views.rename_dashboard),
    url(r'^change_theme/$', views.change_theme),
    url(r'^create_blank_dashboard/$', views.create_blank_dashboard),
    url(r'^add_search/$', views.add_search),
    url(r'^switch_dashboard/$', views.switch_dashboard),
]
