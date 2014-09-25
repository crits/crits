import os

from django.conf import settings
from django.conf.urls import patterns, include, url

urlpatterns = patterns('crits.services.views',
    (r'^list/$', 'list'),
    (r'^analysis_results/list/$', 'analysis_results_listing'),
    (r'^analysis_results/list/(?P<option>\S+)/$', 'analysis_results_listing'),
    (r'^analysis_results/details/(?P<analysis_id>\w+)/$', 'analysis_result'),
    (r'^detail/(?P<name>[\w ]+)/$', 'detail'),
    (r'^enable/(?P<name>[\w ]+)/$', 'enable'),
    (r'^disable/(?P<name>[\w ]+)/$', 'disable'),
    (r'^enable_triage/(?P<name>[\w ]+)/$', 'enable_triage'),
    (r'^disable_triage/(?P<name>[\w ]+)/$', 'disable_triage'),
    (r'^edit/(?P<name>[\w ]+)/$', 'edit_config'),
    (r'^refresh/(?P<crits_type>\w+)/(?P<identifier>\w+)/$', 'refresh_services'),
    (r'^form/(?P<name>[\w ]+)/(?P<crits_type>\w+)/(?P<identifier>\w+)/$', 'get_form'),
    (r'^run/(?P<name>[\w ]+)/(?P<crits_type>\w+)/(?P<identifier>\w+)/$', 'service_run'),
    (r'^delete_task/(?P<crits_type>\w+)/(?P<identifier>\w+)/(?P<task_id>[-\w]+)/$', 'delete_task'),
)

for service_directory in settings.SERVICE_DIRS:
    if os.path.isdir(service_directory):
        for d in os.listdir(service_directory):
            abs_path = os.path.join(service_directory, d, 'urls.py')
            if os.path.isfile(abs_path):
                urlpatterns += patterns('',
                    url(r'^%s/' % d, include('%s.urls' % d)))
