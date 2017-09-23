from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^forge/$', views.add_new_relationship, name='crits-relationships-views-add_new_relationship'),
    url(r'^breakup/$', views.break_relationship, name='crits-relationships-views-break_relationship'),
    url(r'^get_dropdown/$', views.get_relationship_type_dropdown, name='crits-relationships-views-get_relationship_type_dropdown'),
    url(r'^update_relationship_confidence/$', views.update_relationship_confidence, name='crits-relationships-views-update_relationship_confidence'),
    url(r'^update_relationship_reason/$', views.update_relationship_reason, name='crits-relationships-views-update_relationship_reason'),
    url(r'^update_relationship_type/$', views.update_relationship_type, name='crits-relationships-views-update_relationship_type'),
    url(r'^update_relationship_date/$', views.update_relationship_date, name='crits-relationships-views-update_relationship_date'),
]
