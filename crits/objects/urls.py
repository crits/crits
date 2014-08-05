from django.conf.urls import patterns

urlpatterns = patterns('crits.objects.views',
    (r'^add/$', 'add_new_object'),
    (r'^delete/$', 'delete_this_object'),
    (r'^get_dropdown/$', 'get_object_type_dropdown'),
    (r'^update_objects_value/$', 'update_objects_value'),
    (r'^update_objects_source/$', 'update_objects_source'),
    (r'^create_indicator/$', 'indicator_from_object'),
    (r'^bulkadd/$', 'bulk_add_object'),
    (r'^bulkaddinline/$', 'bulk_add_object_inline'),
)
