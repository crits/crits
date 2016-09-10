from django.conf.urls import url

from . import views

urlpatterns = [
        url(r'^upload/$', views.upload_file),
        url(r'^upload/(?P<related_md5>\w+)/$', views.upload_file),
        url(r'^upload_list/(?P<filename>[\S ]+)/(?P<md5s>.+)/$', views.view_upload_list),
        url(r'^bulkadd/$', views.bulk_add_md5_sample),
        url(r'^details/(?P<sample_md5>\w+)/$', views.detail),
        url(r'^strings/(?P<sample_md5>\w+)/$', views.strings),
        url(r'^stackstrings/(?P<sample_md5>\w+)/$', views.stackstrings),
        url(r'^hex/(?P<sample_md5>\w+)/$', views.hex),
        url(r'^xor/(?P<sample_md5>\w+)/$', views.xor),
        url(r'^xor_searcher/(?P<sample_md5>\w+)/$', views.xor_searcher),
        url(r'^unzip/(?P<md5>\w+)/$', views.unzip_sample),
        url(r'^sources/$', views.sources),
        url(r'^remove/(?P<md5>[\S ]+)$', views.remove_sample),
        url(r'^list/$', views.samples_listing),
        url(r'^list/(?P<option>\S+)/$', views.samples_listing),
        url(r'^yarahits/list/$', views.yarahits_listing),
        url(r'^yarahits/list/(?P<option>\S+)/$', views.yarahits_listing),
        url(r'^set_filename/$', views.set_sample_filename),
        url(r'^filenames/$', views.set_sample_filenames),
]
