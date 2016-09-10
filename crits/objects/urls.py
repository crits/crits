from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^add/$', views.add_new_object),
    url(r'^delete/$', views.delete_this_object),
    url(r'^get_dropdown/$', views.get_object_type_dropdown),
    url(r'^update_objects_value/$', views.update_objects_value),
    url(r'^update_objects_source/$', views.update_objects_source),
    url(r'^create_indicator/$', views.indicator_from_object),
    url(r'^bulkadd/$', views.bulk_add_object),
    url(r'^bulkaddinline/$', views.bulk_add_object_inline),
]
