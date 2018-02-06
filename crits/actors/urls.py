from django.conf.urls import url

urlpatterns = [
    url(r'^add/$', 'add_actor', prefix='crits.actors.views'),
    url(r'^add_identifier_type/$', 'new_actor_identifier_type', prefix='crits.actors.views'),
    url(r'^tags/modify/$', 'actor_tags_modify', prefix='crits.actors.views'),
    url(r'^tags/get/$', 'get_actor_tags', prefix='crits.actors.views'),
    url(r'^add_identifier/$', 'add_identifier', prefix='crits.actors.views'),
    url(r'^attribute_identifier/$', 'attribute_identifier', prefix='crits.actors.views'),
    url(r'^edit_identifier/$', 'edit_attributed_identifier', prefix='crits.actors.views'),
    url(r'^remove_identifier/$', 'remove_attributed_identifier', prefix='crits.actors.views'),
    url(r'^edit/name/(?P<id_>\S+)/$', 'edit_actor_name', prefix='crits.actors.views'),
    url(r'^edit/aliases/$', 'edit_actor_aliases', prefix='crits.actors.views'),
    url(r'^search/$', 'actor_search', prefix='crits.actors.views'),
    url(r'^details/(?P<id_>\S+)/$', 'actor_detail', prefix='crits.actors.views'),
    url(r'^remove/(?P<id_>\S+)/$', 'remove_actor', prefix='crits.actors.views'),
    url(r'^list/$', 'actors_listing', prefix='crits.actors.views'),
    url(r'^list/(?P<option>\S+)/$', 'actors_listing', prefix='crits.actors.views'),
    url(r'^identifiers/types/available/$', 'get_actor_identifier_types', prefix='crits.actors.views'),
    url(r'^identifiers/values/available/$', 'get_actor_identifier_type_values', prefix='crits.actors.views'),
    url(r'^identifiers/list/$', 'actor_identifiers_listing', prefix='crits.actors.views'),
    url(r'^identifiers/list/(?P<option>\S+)/$', 'actor_identifiers_listing', prefix='crits.actors.views'),
]
