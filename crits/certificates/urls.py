from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^details/(?P<md5>\w+)/$', views.certificate_details),
    url(r'^upload/$', views.upload_certificate),
    url(r'^remove/(?P<md5>[\S ]+)$', views.remove_certificate),
    url(r'^list/$', views.certificates_listing),
    url(r'^list/(?P<option>\S+)/$', views.certificates_listing),
]
