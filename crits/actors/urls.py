from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^add/$', views.add_actor, name='crits-actors-views-add_actor'),
    url(r'^add_identifier_type/$', views.new_actor_identifier_type, name='crits-actors-views-new_actor_identifier_type'),
    url(r'^tags/modify/$', views.actor_tags_modify, name='crits-actors-views-actor_tags_modify'),
    url(r'^tags/get/$', views.get_actor_tags, name='crits-actors-views-get_actor_tags'),
    url(r'^add_identifier/$', views.add_identifier, name='crits-actors-views-add_identifier'),
    url(r'^attribute_identifier/$', views.attribute_identifier, name='crits-actors-views-attribute_identifier'),
    url(r'^edit_identifier/$', views.edit_attributed_identifier, name='crits-actors-views-edit_attributed_identifier'),
    url(r'^remove_identifier/$', views.remove_attributed_identifier, name='crits-actors-views-remove_attributed_identifier'),
    url(r'^edit/name/(?P<id_>\S+)/$', views.edit_actor_name, name='crits-actors-views-edit_actor_name'),
    url(r'^edit/aliases/$', views.edit_actor_aliases, name='crits-actors-views-edit_actor_aliases'),
    url(r'^search/$', views.actor_search, name='crits-actors-views-actor_search'),
    url(r'^details/(?P<id_>\S+)/$', views.actor_detail, name='crits-actors-views-actor_detail'),
    url(r'^remove/(?P<id_>\S+)/$', views.remove_actor, name='crits-actors-views-remove_actor'),
    url(r'^list/$', views.actors_listing, name='crits-actors-views-actors_listing'),
    url(r'^list/(?P<option>\S+)/$', views.actors_listing, name='crits-actors-views-actors_listing'),
    url(r'^identifiers/types/available/$', views.get_actor_identifier_types, name='crits-actors-views-get_actor_identifier_types'),
    url(r'^identifiers/values/available/$', views.get_actor_identifier_type_values, name='crits-actors-views-get_actor_identifier_type_values'),
    url(r'^identifiers/list/$', views.actor_identifiers_listing, name='crits-actors-views-actor_identifiers_listing'),
    url(r'^identifiers/list/(?P<option>\S+)/$', views.actor_identifiers_listing, name='crits-actors-views-actor_identifiers_listing'),
]
