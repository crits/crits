from __future__ import unicode_literals
from django.conf.urls import url
urlpatterns = [
        url(r'^upload/$', 'upload_file', prefix='crits.samples.views'),
        url(r'^upload/(?P<related_md5>\w+)/$', 'upload_file', prefix='crits.samples.views'),
        url(r'^upload_list/(?P<filename>[\S ]+)/(?P<md5s>.+)/$', 'view_upload_list', prefix='crits.samples.views'),
        url(r'^bulkadd/$', 'bulk_add_md5_sample', prefix='crits.samples.views'),
        url(r'^details/(?P<sample_md5>\w+)/$', 'detail', prefix='crits.samples.views'),
        url(r'^strings/(?P<sample_md5>\w+)/$', 'strings', prefix='crits.samples.views'),
        url(r'^stackstrings/(?P<sample_md5>\w+)/$', 'stackstrings', prefix='crits.samples.views'),
        url(r'^hex/(?P<sample_md5>\w+)/$', 'hex', prefix='crits.samples.views'),
        url(r'^xor/(?P<sample_md5>\w+)/$', 'xor', prefix='crits.samples.views'),
        url(r'^xor_searcher/(?P<sample_md5>\w+)/$', 'xor_searcher', prefix='crits.samples.views'),
        url(r'^unzip/(?P<md5>\w+)/$', 'unzip_sample', prefix='crits.samples.views'),
        url(r'^sources/$', 'sources', prefix='crits.samples.views'),
        url(r'^remove/(?P<md5>[\S ]+)$', 'remove_sample', prefix='crits.samples.views'),
        url(r'^list/$', 'samples_listing', prefix='crits.samples.views'),
        url(r'^list/(?P<option>\S+)/$', 'samples_listing', prefix='crits.samples.views'),
        url(r'^yarahits/list/$', 'yarahits_listing', prefix='crits.samples.views'),
        url(r'^yarahits/list/(?P<option>\S+)/$', 'yarahits_listing', prefix='crits.samples.views'),
        url(r'^set_filename/$', 'set_sample_filename', prefix='crits.samples.views'),
        url(r'^filenames/$', 'set_sample_filenames', prefix='crits.samples.views'),
]
