from django.conf.urls import url

urlpatterns = [
    url(r'^details/(?P<md5>\w+)/$', 'certificate_details', prefix='crits.certificates.views'),
    url(r'^upload/$', 'upload_certificate', prefix='crits.certificates.views'),
    url(r'^remove/(?P<md5>[\S ]+)$', 'remove_certificate', prefix='crits.certificates.views'),
    url(r'^list/$', 'certificates_listing', prefix='crits.certificates.views'),
    url(r'^list/(?P<option>\S+)/$', 'certificates_listing', prefix='crits.certificates.views'),
]
