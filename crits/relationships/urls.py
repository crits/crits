from django.conf.urls import url

urlpatterns = [
    url(r'^forge/$', 'add_new_relationship', prefix='crits.relationships.views'),
    url(r'^breakup/$', 'break_relationship', prefix='crits.relationships.views'),
    url(r'^get_dropdown/$', 'get_relationship_type_dropdown', prefix='crits.relationships.views'),
    url(r'^update_relationship_confidence/$', 'update_relationship_confidence', prefix='crits.relationships.views'),
    url(r'^update_relationship_reason/$', 'update_relationship_reason', prefix='crits.relationships.views'),
    url(r'^update_relationship_type/$', 'update_relationship_type', prefix='crits.relationships.views'),
    url(r'^update_relationship_date/$', 'update_relationship_date', prefix='crits.relationships.views'),
]
