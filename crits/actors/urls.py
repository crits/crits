from __future__ import unicode_literals
from django.conf.urls import patterns

urlpatterns = patterns('crits.actors.views',
    (r'^add/$', 'add_actor'),
    (r'^add_identifier_type/$', 'new_actor_identifier_type'),
    (r'^tags/modify/$', 'actor_tags_modify'),
    (r'^tags/get/$', 'get_actor_tags'),
    (r'^add_identifier/$', 'add_identifier'),
    (r'^attribute_identifier/$', 'attribute_identifier'),
    (r'^edit_identifier/$', 'edit_attributed_identifier'),
    (r'^remove_identifier/$', 'remove_attributed_identifier'),
    (r'^edit/name/(?P<id_>\S+)/$', 'edit_actor_name'),
    (r'^edit/aliases/$', 'edit_actor_aliases'),
    (r'^search/$', 'actor_search'),
    (r'^details/(?P<id_>\S+)/$', 'actor_detail'),
    (r'^remove/(?P<id_>\S+)/$', 'remove_actor'),
    (r'^list/$', 'actors_listing'),
    (r'^list/(?P<option>\S+)/$', 'actors_listing'),
    (r'^identifiers/types/available/$', 'get_actor_identifier_types'),
    (r'^identifiers/values/available/$', 'get_actor_identifier_type_values'),
    (r'^identifiers/list/$', 'actor_identifiers_listing'),
    (r'^identifiers/list/(?P<option>\S+)/$', 'actor_identifiers_listing'),
)
