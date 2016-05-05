from django.conf.urls import url

urlpatterns = [
    url(r'^poll/$', 'poll', prefix='crits.notifications.views'),
    url(r'^ack/$', 'acknowledge', prefix='crits.notifications.views'),
]
