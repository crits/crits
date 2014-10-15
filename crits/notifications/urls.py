from django.conf.urls import patterns

urlpatterns = patterns('crits.notifications.views',
    (r'^poll/$', 'poll'),
    (r'^ack/$', 'acknowledge'),
)
