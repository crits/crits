import os

from django.conf import settings
from django.conf.urls import include, url

urlpatterns = [
    url(r'^list/$', 'list', prefix='crits.services.views'),
    url(r'^analysis_results/list/$', 'analysis_results_listing', prefix='crits.services.views'),
    url(r'^analysis_results/list/(?P<option>\S+)/$', 'analysis_results_listing', prefix='crits.services.views'),
    url(r'^analysis_results/details/(?P<analysis_id>\w+)/$', 'analysis_result', prefix='crits.services.views'),
    url(r'^detail/(?P<name>[\w ]+)/$', 'detail', prefix='crits.services.views'),
    url(r'^enable/(?P<name>[\w ]+)/$', 'enable', prefix='crits.services.views'),
    url(r'^disable/(?P<name>[\w ]+)/$', 'disable', prefix='crits.services.views'),
    url(r'^enable_triage/(?P<name>[\w ]+)/$', 'enable_triage', prefix='crits.services.views'),
    url(r'^disable_triage/(?P<name>[\w ]+)/$', 'disable_triage', prefix='crits.services.views'),
    url(r'^edit/(?P<name>[\w ]+)/$', 'edit_config', prefix='crits.services.views'),
    url(r'^refresh/(?P<crits_type>\w+)/(?P<identifier>\w+)/$', 'refresh_services', prefix='crits.services.views'),
    url(r'^form/(?P<name>[\w ]+)/(?P<crits_type>\w+)/(?P<identifier>\w+)/$', 'get_form', prefix='crits.services.views'),
    url(r'^run/(?P<name>[\w ]+)/(?P<crits_type>\w+)/(?P<identifier>\w+)/$', 'service_run', prefix='crits.services.views'),
    url(r'^delete_task/(?P<crits_type>\w+)/(?P<identifier>\w+)/(?P<task_id>[-\w]+)/$', 'delete_task', prefix='crits.services.views'),
]

for service_directory in settings.SERVICE_DIRS:
    if os.path.isdir(service_directory):
        for d in os.listdir(service_directory):
            abs_path = os.path.join(service_directory, d, 'urls.py')
            if os.path.isfile(abs_path):
                urlpatterns.append(
                    url(r'^%s/' % d, include('%s.urls' % d)))
