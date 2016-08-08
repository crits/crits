from django.conf.urls import url
from django.contrib.auth.views import logout_then_login

urlpatterns = [

    # Authentication
    url(r'^login/$', 'crits.core.views.login'),
    url(r'^logout/$', logout_then_login),

    # Buckets
    url(r'^bucket/list/$', 'crits.core.views.bucket_list'),
    url(r'^bucket/list/(?P<option>.+)$', 'crits.core.views.bucket_list'),
    url(r'^bucket/mod/$', 'crits.core.views.bucket_modify'),
    url(r'^bucket/autocomplete/$', 'crits.core.views.bucket_autocomplete'),
    url(r'^bucket/promote/$', 'crits.core.views.bucket_promote'),

    # Common functionality for all TLOs
    url(r'^status/update/(?P<type_>\S+)/(?P<id_>\S+)/$', 'crits.core.views.update_status'),
    url(r'^search/$', 'crits.core.views.global_search_listing'),
    url(r'^object/download/$', 'crits.core.views.download_object'),
    url(r'^files/download/(?P<sample_md5>\w+)/$', 'crits.core.views.download_file'),
    url(r'^object/sources/removeall/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', 'crits.core.views.remove_all_source'),
    url(r'^object/sources/remove/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', 'crits.core.views.remove_source'),
    url(r'^object/sources/(?P<method>\S+)/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', 'crits.core.views.add_update_source'),
    url(r'^source_releasability/$', 'crits.core.views.source_releasability'),
    url(r'^tickets/(?P<method>\S+)/(?P<type_>\w+)/(?P<id_>\w+)/$', 'crits.core.views.add_update_ticket'),
    url(r'^preferred_actions/$', 'crits.core.views.add_preferred_actions'),
    url(r'^actions/(?P<method>\S+)/(?P<obj_type>\S+)/(?P<obj_id>\w+)/$', 'crits.core.views.add_update_action'),
    url(r'^action/remove/(?P<obj_type>\S+)/(?P<obj_id>\w+)/$', 'crits.core.views.remove_action'),
    url(r'^add_action/$', 'crits.core.views.new_action'),
    url(r'^get_actions_for_tlo/$', 'crits.core.views.get_actions_for_tlo'),


    # CRITs Configuration
    url(r'^config/$', 'crits.config.views.crits_config'),
    url(r'^modify_config/$', 'crits.config.views.modify_config'),
    url(r'^audit/list/$', 'crits.core.views.audit_listing'),
    url(r'^audit/list/(?P<option>\S+)/$', 'crits.core.views.audit_listing'),
    url(r'^items/editor/$', 'crits.core.views.item_editor'),
    url(r'^items/list/$', 'crits.core.views.items_listing'),
    url(r'^items/list/(?P<itype>\S+)/(?P<option>\S+)/$', 'crits.core.views.items_listing'),
    url(r'^items/toggle_active/$', 'crits.core.views.toggle_item_active'),
    url(r'^users/toggle_active/$', 'crits.core.views.toggle_user_active'),
    url(r'^users/list/$', 'crits.core.views.users_listing'),
    url(r'^users/list/(?P<option>\S+)/$', 'crits.core.views.users_listing'),
    url(r'^get_item_data/$', 'crits.core.views.get_item_data'),
    url(r'^add_action/$', 'crits.core.views.new_action'),

    # Default landing page
    url(r'^$', 'crits.dashboards.views.dashboard'),
    url(r'^counts/list/$', 'crits.core.views.counts_listing'),
    url(r'^counts/list/(?P<option>\S+)/$', 'crits.core.views.counts_listing'),

    # Dialogs
    url(r'^get_dialog/(?P<dialog>[A-Za-z0-9\-\._-]+)$', 'crits.core.views.get_dialog'),
    url(r'^get_dialog/$', 'crits.core.views.get_dialog'),

    # General core pages
    url(r'^details/(?P<type_>\S+)/(?P<id_>\S+)/$', 'crits.core.views.details'),
    url(r'^update_object_description/', 'crits.core.views.update_object_description'),
    url(r'^update_object_data/', 'crits.core.views.update_object_data'),

    # Helper pages
    url(r'^about/$', 'crits.core.views.about'),
    url(r'^help/$', 'crits.core.views.help'),
    url(r'^get_search_help/$', 'crits.core.views.get_search_help'),

    # Sectors
    url(r'^sector/list/$', 'crits.core.views.sector_list'),
    url(r'^sector/list/(?P<option>.+)$', 'crits.core.views.sector_list'),
    url(r'^sector/mod/$', 'crits.core.views.sector_modify'),
    url(r'^sector/options/$', 'crits.core.views.get_available_sectors'),

    # Timeline
    url(r'^timeline/(?P<data_type>\S+)/$', 'crits.core.views.timeline'),
    url(r'^timeline/(?P<data_type>\S+)/(?P<extra_data>\S+)/$', 'crits.core.views.timeline'),
    url(r'^timeline/$', 'crits.core.views.timeline'),

    # User Stuff
    url(r'^profile/(?P<user>\S+)/$', 'crits.core.views.profile'),
    url(r'^profile/$', 'crits.core.views.profile'),
    url(r'^source_access/$', 'crits.core.views.source_access'),
    url(r'^source_add/$', 'crits.core.views.source_add'),
    url(r'^get_user_source_list/$', 'crits.core.views.get_user_source_list'),
    url(r'^user_role_add/$', 'crits.core.views.user_role_add'),
    url(r'^user_source_access/$', 'crits.core.views.user_source_access'),
    url(r'^user_source_access/(?P<username>\S+)/$', 'crits.core.views.user_source_access'),
    url(r'^preference_toggle/(?P<section>\S+)/(?P<setting>\S+)/$', 'crits.core.views.user_preference_toggle'),
    url(r'^preference_update/(?P<section>\S+)/$', 'crits.core.views.user_preference_update'),
    url(r'^clear_user_notifications/$', 'crits.core.views.clear_user_notifications'),
    url(r'^delete_user_notification/(?P<type_>\S+)/(?P<oid>\S+)/$', 'crits.core.views.delete_user_notification'),
    url(r'^change_subscription/(?P<stype>\S+)/(?P<oid>\S+)/$', 'crits.core.views.change_subscription'),
    url(r'^source_subscription/$', 'crits.core.views.source_subscription'),
    url(r'^change_password/$', 'crits.core.views.change_password'),
    url(r'^change_totp_pin/$', 'crits.core.views.change_totp_pin'),
    url(r'^reset_password/$', 'crits.core.views.reset_password'),
    url(r'^favorites/toggle/$', 'crits.core.views.toggle_favorite'),
    url(r'^favorites/view/$', 'crits.core.views.favorites'),
    url(r'^favorites/list/(?P<ctype>\S+)/(?P<option>\S+)/$', 'crits.core.views.favorites_list'),

    # User API Authentication
    url(r'^get_api_key/$', 'crits.core.views.get_api_key'),
    url(r'^create_api_key/$', 'crits.core.views.create_api_key'),
    url(r'^make_default_api_key/$', 'crits.core.views.make_default_api_key'),
    url(r'^revoke_api_key/$', 'crits.core.views.revoke_api_key'),

]
