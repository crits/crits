from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^poll/$', views.poll, name='crits-notifications-views-poll'),
    url(r'^ack/$', views.acknowledge, name='crits-notifications-views-acknowledge'),
]
