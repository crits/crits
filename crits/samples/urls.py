from __future__ import unicode_literals
from django.conf.urls import patterns

urlpatterns = patterns('crits.samples.views',
        (r'^upload/$', 'upload_file'),
        (r'^upload/(?P<related_md5>\w+)/$', 'upload_file'),
        (r'^upload_list/(?P<filename>[\S ]+)/(?P<md5s>.+)/$', 'view_upload_list'),
        (r'^bulkadd/$', 'bulk_add_md5_sample'),
        (r'^details/(?P<sample_md5>\w+)/$', 'detail'),
        (r'^strings/(?P<sample_md5>\w+)/$', 'strings'),
        (r'^stackstrings/(?P<sample_md5>\w+)/$', 'stackstrings'),
        (r'^hex/(?P<sample_md5>\w+)/$', 'hex'),
        (r'^xor/(?P<sample_md5>\w+)/$', 'xor'),
        (r'^xor_searcher/(?P<sample_md5>\w+)/$', 'xor_searcher'),
        (r'^unzip/(?P<md5>\w+)/$', 'unzip_sample'),
        (r'^sources/$', 'sources'),
        (r'^remove/(?P<md5>[\S ]+)$', 'remove_sample'),
        (r'^list/$', 'samples_listing'),
        (r'^list/(?P<option>\S+)/$', 'samples_listing'),
        (r'^yarahits/list/$', 'yarahits_listing'),
        (r'^yarahits/list/(?P<option>\S+)/$', 'yarahits_listing'),
        (r'^set_filename/$', 'set_sample_filename'),
        (r'^filenames/$', 'set_sample_filenames'),
)
