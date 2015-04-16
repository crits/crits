from django.conf.urls import patterns
from django.contrib.auth.views import logout_then_login

urlpatterns = patterns('',

    # Authentication
    (r'^login/$', 'crits.core.views.login'),
    (r'^logout/$', logout_then_login),

    # Buckets
    (r'^bucket/list/$', 'crits.core.views.bucket_list'),
    (r'^bucket/list/(?P<option>.+)$', 'crits.core.views.bucket_list'),
    (r'^bucket/mod/$', 'crits.core.views.bucket_modify'),
    (r'^bucket/autocomplete/$', 'crits.core.views.bucket_autocomplete'),
    (r'^bucket/promote/$', 'crits.core.views.bucket_promote'),

    # Common functionality for all TLOs
    (r'^status/update/(?P<type_>\S+)/(?P<id_>\S+)/$', 'crits.core.views.update_status'),
    (r'^search/$', 'crits.core.views.global_search_listing'),
    (r'^object/download/$', 'crits.core.views.download_object'),
    (r'^files/download/(?P<sample_md5>\w+)/$', 'crits.core.views.download_file'),
    (r'^object/sources/removeall/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', 'crits.core.views.remove_all_source'),
    (r'^object/sources/remove/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', 'crits.core.views.remove_source'),
    (r'^object/sources/(?P<method>\S+)/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', 'crits.core.views.add_update_source'),
    (r'^source_releasability/$', 'crits.core.views.source_releasability'),
    (r'^tickets/(?P<method>\S+)/(?P<type_>\w+)/(?P<id_>\w+)/$', 'crits.core.views.add_update_ticket'),

    # CRITs Configuration
    (r'^config/$', 'crits.config.views.crits_config'),
    (r'^modify_config/$', 'crits.config.views.modify_config'),
    (r'^audit/list/$', 'crits.core.views.audit_listing'),
    (r'^audit/list/(?P<option>\S+)/$', 'crits.core.views.audit_listing'),
    (r'^items/editor/$', 'crits.core.views.item_editor'),
    (r'^items/list/$', 'crits.core.views.items_listing'),
    (r'^items/list/(?P<itype>\S+)/(?P<option>\S+)/$', 'crits.core.views.items_listing'),
    (r'^items/toggle_active/$', 'crits.core.views.toggle_item_active'),
    (r'^users/toggle_active/$', 'crits.core.views.toggle_user_active'),
    (r'^users/list/$', 'crits.core.views.users_listing'),
    (r'^users/list/(?P<option>\S+)/$', 'crits.core.views.users_listing'),
    (r'^get_item_data/$', 'crits.core.views.get_item_data'),

    # Default landing page
    (r'^$', 'crits.dashboards.views.dashboard'),
    (r'^counts/list/$', 'crits.core.views.counts_listing'),
    (r'^counts/list/(?P<option>\S+)/$', 'crits.core.views.counts_listing'),

    # Dialogs
    (r'^get_dialog/(?P<dialog>[A-Za-z0-9\-\._-]+)$', 'crits.core.views.get_dialog'),
    (r'^get_dialog/$', 'crits.core.views.get_dialog'),

    # General core pages
    (r'^details/(?P<type_>\S+)/(?P<id_>\S+)/$', 'crits.core.views.details'),
    (r'^update_object_description/', 'crits.core.views.update_object_description'),

    # Helper pages
    (r'^about/$', 'crits.core.views.about'),
    (r'^help/$', 'crits.core.views.help'),
    (r'^get_search_help/$', 'crits.core.views.get_search_help'),

    # Sectors
    (r'^sector/list/$', 'crits.core.views.sector_list'),
    (r'^sector/list/(?P<option>.+)$', 'crits.core.views.sector_list'),
    (r'^sector/mod/$', 'crits.core.views.sector_modify'),
    (r'^sector/options/$', 'crits.core.views.get_available_sectors'),

    # Timeline
    (r'^timeline/(?P<data_type>\S+)/$', 'crits.core.views.timeline'),
    (r'^timeline/(?P<data_type>\S+)/(?P<extra_data>\S+)/$', 'crits.core.views.timeline'),
    (r'^timeline/$', 'crits.core.views.timeline'),

    # User Stuff
    (r'^profile/(?P<user>\S+)/$', 'crits.core.views.profile'),
    (r'^profile/$', 'crits.core.views.profile'),
    (r'^source_access/$', 'crits.core.views.source_access'),
    (r'^source_add/$', 'crits.core.views.source_add'),
    (r'^get_user_source_list/$', 'crits.core.views.get_user_source_list'),
    (r'^user_role_add/$', 'crits.core.views.user_role_add'),
    (r'^user_source_access/$', 'crits.core.views.user_source_access'),
    (r'^user_source_access/(?P<username>\S+)/$', 'crits.core.views.user_source_access'),
    (r'^preference_toggle/(?P<section>\S+)/(?P<setting>\S+)/$', 'crits.core.views.user_preference_toggle'),
    (r'^preference_update/(?P<section>\S+)/$', 'crits.core.views.user_preference_update'),
    (r'^clear_user_notifications/$', 'crits.core.views.clear_user_notifications'),
    (r'^delete_user_notification/(?P<type_>\S+)/(?P<oid>\S+)/$', 'crits.core.views.delete_user_notification'),
    (r'^change_subscription/(?P<stype>\S+)/(?P<oid>\S+)/$', 'crits.core.views.change_subscription'),
    (r'^source_subscription/$', 'crits.core.views.source_subscription'),
    (r'^change_password/$', 'crits.core.views.change_password'),
    (r'^change_totp_pin/$', 'crits.core.views.change_totp_pin'),
    (r'^reset_password/$', 'crits.core.views.reset_password'),
    (r'^favorites/toggle/$', 'crits.core.views.toggle_favorite'),
    (r'^favorites/view/$', 'crits.core.views.favorites'),
    (r'^favorites/list/(?P<ctype>\S+)/(?P<option>\S+)/$', 'crits.core.views.favorites_list'),

    # User API Authentication
    (r'^get_api_key/$', 'crits.core.views.get_api_key'),
    (r'^create_api_key/$', 'crits.core.views.create_api_key'),
    (r'^make_default_api_key/$', 'crits.core.views.make_default_api_key'),
    (r'^revoke_api_key/$', 'crits.core.views.revoke_api_key'),

)
