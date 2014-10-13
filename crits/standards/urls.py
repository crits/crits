from django.conf.urls import patterns

urlpatterns = patterns('crits.standards.views',
    (r'^upload/$', 'upload_standards'),
)
