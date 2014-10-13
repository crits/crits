from django.conf.urls import patterns

urlpatterns = patterns('crits.samples.views',
        #disassembly
        (r'^disassembly/details/(?P<_id>\w+)/$', 'crits.disassembly.views.disassembly_details'),
        (r'^disassembly/details_by_link/(?P<link>.+)/$', 'crits.disassembly.views.details_by_link'),
        (r'^disassembly/get_versions/(?P<_id>\w+)/$', 'crits.disassembly.views.get_disassembly_versions'),
        (r'^disassembly/set_description/(?P<_id>\w+)/$', 'crits.disassembly.views.set_disassembly_description'),
        (r'^disassembly/set_tool_details/(?P<_id>\w+)/$', 'crits.disassembly.views.set_disassembly_tool_details'),
        (r'^disassembly/set_tool_name/(?P<_id>\w+)/$', 'crits.disassembly.views.set_disassembly_tool_name'),
        (r'^disassembly/set_disassembly_type/(?P<_id>\w+)/$', 'crits.disassembly.views.set_disassembly_type'),
        (r'^disassembly/upload/(?P<link_id>.+)/$', 'crits.disassembly.views.upload_disassembly'),
        (r'^disassembly/upload/$', 'crits.disassembly.views.upload_disassembly'),
        (r'^disassembly/remove/(?P<_id>[\S ]+)$', 'crits.disassembly.views.remove_disassembly'),
        (r'^disassembly/list/$', 'crits.disassembly.views.disassembly_listing'),
        (r'^disassembly/list/(?P<option>\S+)/$', 'crits.disassembly.views.disassembly_listing'),
        (r'^disassembly/add_data_type/$', 'crits.disassembly.views.new_disassembly_type'),
        (r'^disassembly/get_data_types/$', 'crits.disassembly.views.get_disassembly_type_dropdown'),
