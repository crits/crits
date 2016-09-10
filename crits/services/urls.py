import os

from django.conf import settings
from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^list/$', views.list),
    url(r'^analysis_results/list/$', views.analysis_results_listing),
    url(r'^analysis_results/list/(?P<option>\S+)/$', views.analysis_results_listing),
    url(r'^analysis_results/details/(?P<analysis_id>\w+)/$', views.analysis_result),
    url(r'^detail/(?P<name>[\w ]+)/$', views.detail),
    url(r'^enable/(?P<name>[\w ]+)/$', views.enable),
    url(r'^disable/(?P<name>[\w ]+)/$', views.disable),
    url(r'^enable_triage/(?P<name>[\w ]+)/$', views.enable_triage),
    url(r'^disable_triage/(?P<name>[\w ]+)/$', views.disable_triage),
    url(r'^edit/(?P<name>[\w ]+)/$', views.edit_config),
    url(r'^refresh/(?P<crits_type>\w+)/(?P<identifier>\w+)/$', views.refresh_services),
    url(r'^form/(?P<name>[\w ]+)/(?P<crits_type>\w+)/(?P<identifier>\w+)/$', views.get_form),
    url(r'^run/(?P<name>[\w ]+)/(?P<crits_type>\w+)/(?P<identifier>\w+)/$', views.service_run),
    url(r'^delete_task/(?P<crits_type>\w+)/(?P<identifier>\w+)/(?P<task_id>[-\w]+)/$', views.delete_task),
]

for service_directory in settings.SERVICE_DIRS:
    if os.path.isdir(service_directory):
        for d in os.listdir(service_directory):
            abs_path = os.path.join(service_directory, d, 'urls.py')
            if os.path.isfile(abs_path):
                urlpatterns.append(
                    url(r'^%s/' % d, include('%s.urls' % d)))
