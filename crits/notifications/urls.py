from __future__ import unicode_literals
from django.conf.urls import patterns

urlpatterns = patterns('crits.notifications.views',
    (r'^poll/$', 'poll'),
    (r'^ack/$', 'acknowledge'),
)
