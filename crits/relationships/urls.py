from django.conf.urls import patterns

urlpatterns = patterns('crits.relationships.views',
    (r'^forge/$', 'add_new_relationship'),
    (r'^breakup/$', 'break_relationship'),
    (r'^get_dropdown/$', 'get_relationship_type_dropdown'),
    (r'^update_relationship_confidence/$', 'update_relationship_confidence'),
    (r'^update_relationship_reason/$', 'update_relationship_reason'),
    (r'^update_relationship_type/$', 'update_relationship_type'),
    (r'^update_relationship_date/$', 'update_relationship_date'),
)
