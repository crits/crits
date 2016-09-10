from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^poll/$', views.poll),
    url(r'^ack/$', views.acknowledge),
]
