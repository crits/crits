from django.conf.urls import url

urlpatterns = [
    url(r'^add/$', 'add_new_object', prefix='crits.objects.views'),
    url(r'^delete/$', 'delete_this_object', prefix='crits.objects.views'),
    url(r'^get_dropdown/$', 'get_object_type_dropdown', prefix='crits.objects.views'),
    url(r'^update_objects_value/$', 'update_objects_value', prefix='crits.objects.views'),
    url(r'^update_objects_source/$', 'update_objects_source', prefix='crits.objects.views'),
    url(r'^create_indicator/$', 'indicator_from_object', prefix='crits.objects.views'),
    url(r'^bulkadd/$', 'bulk_add_object', prefix='crits.objects.views'),
    url(r'^bulkaddinline/$', 'bulk_add_object_inline', prefix='crits.objects.views'),
]
