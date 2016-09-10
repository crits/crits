from django.conf.urls import url
from django.contrib.auth.views import logout_then_login

from . import views

from crits.config.views import crits_config, modify_config
from crits.dashboards.views import dashboard

urlpatterns = [

    # Authentication
    url(r'^login/$', views.login),
    url(r'^logout/$', logout_then_login),

    # Buckets
    url(r'^bucket/list/$', views.bucket_list),
    url(r'^bucket/list/(?P<option>.+)$', views.bucket_list),
    url(r'^bucket/mod/$', views.bucket_modify),
    url(r'^bucket/autocomplete/$', views.bucket_autocomplete),
    url(r'^bucket/promote/$', views.bucket_promote),

    # Common functionality for all TLOs
    url(r'^status/update/(?P<type_>\S+)/(?P<id_>\S+)/$', views.update_status),
    url(r'^search/$', views.global_search_listing),
    url(r'^object/download/$', views.download_object),
    url(r'^files/download/(?P<sample_md5>\w+)/$', views.download_file),
    url(r'^object/sources/removeall/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', views.remove_all_source),
    url(r'^object/sources/remove/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', views.remove_source),
    url(r'^object/sources/(?P<method>\S+)/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', views.add_update_source),
    url(r'^source_releasability/$', views.source_releasability),
    url(r'^tickets/(?P<method>\S+)/(?P<type_>\w+)/(?P<id_>\w+)/$', views.add_update_ticket),
    url(r'^preferred_actions/$', views.add_preferred_actions),
    url(r'^actions/(?P<method>\S+)/(?P<obj_type>\S+)/(?P<obj_id>\w+)/$', views.add_update_action),
    url(r'^action/remove/(?P<obj_type>\S+)/(?P<obj_id>\w+)/$', views.remove_action),
    url(r'^add_action/$', views.new_action),
    url(r'^get_actions_for_tlo/$', views.get_actions_for_tlo),


    # CRITs Configuration
    url(r'^config/$', crits_config),
    url(r'^modify_config/$', modify_config),
    url(r'^audit/list/$', views.audit_listing),
    url(r'^audit/list/(?P<option>\S+)/$', views.audit_listing),
    url(r'^items/editor/$', views.item_editor),
    url(r'^items/list/$', views.items_listing),
    url(r'^items/list/(?P<itype>\S+)/(?P<option>\S+)/$', views.items_listing),
    url(r'^items/toggle_active/$', views.toggle_item_active),
    url(r'^users/toggle_active/$', views.toggle_user_active),
    url(r'^users/list/$', views.users_listing),
    url(r'^users/list/(?P<option>\S+)/$', views.users_listing),
    url(r'^get_item_data/$', views.get_item_data),
    url(r'^add_action/$', views.new_action),

    # Default landing page
    url(r'^$', dashboard),
    url(r'^counts/list/$', views.counts_listing),
    url(r'^counts/list/(?P<option>\S+)/$', views.counts_listing),

    # Dialogs
    url(r'^get_dialog/(?P<dialog>[A-Za-z0-9\-\._-]+)$', views.get_dialog),
    url(r'^get_dialog/$', views.get_dialog),

    # General core pages
    url(r'^details/(?P<type_>\S+)/(?P<id_>\S+)/$', views.details),
    url(r'^update_object_description/', views.update_object_description),
    url(r'^update_object_data/', views.update_object_data),

    # Helper pages
    url(r'^about/$', views.about),
    url(r'^help/$', views.help),
    url(r'^get_search_help/$', views.get_search_help),

    # Sectors
    url(r'^sector/list/$', views.sector_list),
    url(r'^sector/list/(?P<option>.+)$', views.sector_list),
    url(r'^sector/mod/$', views.sector_modify),
    url(r'^sector/options/$', views.get_available_sectors),

    # Timeline
    url(r'^timeline/(?P<data_type>\S+)/$', views.timeline),
    url(r'^timeline/(?P<data_type>\S+)/(?P<extra_data>\S+)/$', views.timeline),
    url(r'^timeline/$', views.timeline),

    # User Stuff
    url(r'^profile/(?P<user>\S+)/$', views.profile),
    url(r'^profile/$', views.profile),
    url(r'^source_access/$', views.source_access),
    url(r'^source_add/$', views.source_add),
    url(r'^get_user_source_list/$', views.get_user_source_list),
    url(r'^user_role_add/$', views.user_role_add),
    url(r'^user_source_access/$', views.user_source_access),
    url(r'^user_source_access/(?P<username>\S+)/$', views.user_source_access),
    url(r'^preference_toggle/(?P<section>\S+)/(?P<setting>\S+)/$', views.user_preference_toggle),
    url(r'^preference_update/(?P<section>\S+)/$', views.user_preference_update),
    url(r'^clear_user_notifications/$', views.clear_user_notifications),
    url(r'^delete_user_notification/(?P<type_>\S+)/(?P<oid>\S+)/$', views.delete_user_notification),
    url(r'^change_subscription/(?P<stype>\S+)/(?P<oid>\S+)/$', views.change_subscription),
    url(r'^source_subscription/$', views.source_subscription),
    url(r'^change_password/$', views.change_password),
    url(r'^change_totp_pin/$', views.change_totp_pin),
    url(r'^reset_password/$', views.reset_password),
    url(r'^favorites/toggle/$', views.toggle_favorite),
    url(r'^favorites/view/$', views.favorites),
    url(r'^favorites/list/(?P<ctype>\S+)/(?P<option>\S+)/$', views.favorites_list),

    # User API Authentication
    url(r'^get_api_key/$', views.get_api_key),
    url(r'^create_api_key/$', views.create_api_key),
    url(r'^make_default_api_key/$', views.make_default_api_key),
    url(r'^revoke_api_key/$', views.revoke_api_key),

]
