from django.conf.urls import url
from django.contrib.auth.views import logout_then_login

from . import views

from crits.config import views as cviews
# crits_config, modify_config
from crits.dashboards import views as dviews

urlpatterns = [

    # Authentication
    url(r'^login/$', views.login, name='crits-core-views-login'),
    url(r'^logout/$', logout_then_login, name='crits-core-views-logout_then_login'),

    # Buckets
    url(r'^bucket/list/$', views.bucket_list, name='crits-core-views-bucket_list'),
    url(r'^bucket/list/(?P<option>.+)$', views.bucket_list, name='crits-core-views-bucket_list'),
    url(r'^bucket/mod/$', views.bucket_modify, name='crits-core-views-bucket_modify'),
    url(r'^bucket/autocomplete/$', views.bucket_autocomplete, name='crits-core-views-bucket_autocomplete'),
    url(r'^bucket/promote/$', views.bucket_promote, name='crits-core-views-bucket_promote'),

    # Common functionality for all TLOs
    url(r'^status/update/(?P<type_>\S+)/(?P<id_>\S+)/$', views.update_status, name='crits-core-views-update_status'),
    url(r'^search/$', views.global_search_listing, name='crits-core-views-global_search_listing'),
    url(r'^object/download/$', views.download_object, name='crits-core-views-download_object'),
    url(r'^files/download/(?P<sample_md5>\w+)/$', views.download_file, name='crits-core-views-download_file'),
    url(r'^object/sources/removeall/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', views.remove_all_source, name='crits-core-views-remove_all_source'),
    url(r'^object/sources/remove/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', views.remove_source, name='crits-core-views-remove_source'),
    url(r'^object/sources/(?P<method>\S+)/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', views.add_update_source, name='crits-core-views-add_update_source'),
    url(r'^source_releasability/$', views.source_releasability, name='crits-core-views-source_releasability'),
    url(r'^tickets/(?P<method>\S+)/(?P<type_>\w+)/(?P<id_>\w+)/$', views.add_update_ticket, name='crits-core-views-add_update_ticket'),
    url(r'^preferred_actions/$', views.add_preferred_actions, name='crits-core-views-add_preferred_actions'),
    url(r'^actions/(?P<method>\S+)/(?P<obj_type>\S+)/(?P<obj_id>\w+)/$', views.add_update_action, name='crits-core-views-add_update_action'),
    url(r'^action/remove/(?P<obj_type>\S+)/(?P<obj_id>\w+)/$', views.remove_action, name='crits-core-views-remove_action'),
    url(r'^add_action/$', views.new_action, name='crits-core-views-new_action'),
    url(r'^get_actions_for_tlo/$', views.get_actions_for_tlo, name='crits-core-views-get_actions_for_tlo'),


    # CRITs Configuration
    url(r'^config/$', cviews.crits_config, name='crits-config-views-crits_config'),
    url(r'^modify_config/$', cviews.modify_config, name='crits-config-views-modify_config'),
    url(r'^audit/list/$', views.audit_listing, name='crits-core-views-audit_listing'),
    url(r'^audit/list/(?P<option>\S+)/$', views.audit_listing, name='crits-core-views-audit_listing'),
    url(r'^items/editor/$', views.item_editor, name='crits-core-views-item_editor'),
    url(r'^items/list/$', views.items_listing, name='crits-core-views-items_listing'),
    url(r'^items/list/(?P<itype>\S+)/(?P<option>\S+)/$', views.items_listing, name='crits-core-views-items_listing'),
    url(r'^items/toggle_active/$', views.toggle_item_active, name='crits-core-views-toggle_item_active'),
    url(r'^users/toggle_active/$', views.toggle_user_active, name='crits-core-views-toggle_user_active'),
    url(r'^users/list/$', views.users_listing, name='crits-core-views-users_listing'),
    url(r'^users/list/(?P<option>\S+)/$', views.users_listing, name='crits-core-views-users_listing'),
    url(r'^get_item_data/$', views.get_item_data, name='crits-core-views-get_item_data'),
    url(r'^add_action/$', views.new_action, name='crits-core-views-new_action'),

    # Default landing page
    url(r'^$', dviews.dashboard, name='crits-dashboards-views-dashboard'),
    url(r'^counts/list/$', views.counts_listing, name='crits-core-views-counts_listing'),
    url(r'^counts/list/(?P<option>\S+)/$', views.counts_listing, name='crits-core-views-counts_listing'),

    # Dialogs
    url(r'^get_dialog/(?P<dialog>[A-Za-z0-9\-\._-]+)$', views.get_dialog, name='crits-core-views-get_dialog'),
    url(r'^get_dialog/$', views.get_dialog, name='crits-core-views-get_dialog'),

    # General core pages
    url(r'^details/(?P<type_>\S+)/(?P<id_>\S+)/$', views.details, name='crits-core-views-details'),
    url(r'^update_object_description/', views.update_object_description, name='crits-core-views-update_object_description'),
    url(r'^update_object_data/', views.update_object_data, name='crits-core-views-update_object_data'),

    # Helper pages
    url(r'^about/$', views.about, name='crits-core-views-about'),
    url(r'^help/$', views.help, name='crits-core-views-help'),
    url(r'^get_search_help/$', views.get_search_help, name='crits-core-views-get_search_help'),

    # Sectors
    url(r'^sector/list/$', views.sector_list, name='crits-core-views-sector_list'),
    url(r'^sector/list/(?P<option>.+)$', views.sector_list, name='crits-core-views-sector_list'),
    url(r'^sector/mod/$', views.sector_modify, name='crits-core-views-sector_modify'),
    url(r'^sector/options/$', views.get_available_sectors, name='crits-core-views-get_available_sectors'),

    # Timeline
    url(r'^timeline/(?P<data_type>\S+)/$', views.timeline, name='crits-core-views-timeline'),
    url(r'^timeline/(?P<data_type>\S+)/(?P<extra_data>\S+)/$', views.timeline, name='crits-core-views-timeline'),
    url(r'^timeline/$', views.timeline, name='crits-core-views-timeline'),

    # User Stuff
    url(r'^profile/(?P<user>\S+)/$', views.profile, name='crits-core-views-profile'),
    url(r'^profile/$', views.profile, name='crits-core-views-profile'),
    url(r'^source_access/$', views.source_access, name='crits-core-views-source_access'),
    url(r'^source_add/$', views.source_add, name='crits-core-views-source_add'),
    url(r'^get_user_source_list/$', views.get_user_source_list, name='crits-core-views-get_user_source_list'),
    url(r'^user_role_add/$', views.user_role_add, name='crits-core-views-user_role_add'),
    url(r'^user_source_access/$', views.user_source_access, name='crits-core-views-user_source_access'),
    url(r'^user_source_access/(?P<username>\S+)/$', views.user_source_access, name='crits-core-views-user_source_access'),
    url(r'^preference_toggle/(?P<section>\S+)/(?P<setting>\S+)/$', views.user_preference_toggle, name='crits-core-views-user_preference_toggle'),
    url(r'^preference_update/(?P<section>\S+)/$', views.user_preference_update, name='crits-core-views-user_preference_update'),
    url(r'^clear_user_notifications/$', views.clear_user_notifications, name='crits-core-views-clear_user_notifications'),
    url(r'^delete_user_notification/(?P<type_>\S+)/(?P<oid>\S+)/$', views.delete_user_notification, name='crits-core-views-delete_user_notification'),
    url(r'^change_subscription/(?P<stype>\S+)/(?P<oid>\S+)/$', views.change_subscription, name='crits-core-views-change_subscription'),
    url(r'^source_subscription/$', views.source_subscription, name='crits-core-views-source_subscription'),
    url(r'^change_password/$', views.change_password, name='crits-core-views-change_password'),
    url(r'^change_totp_pin/$', views.change_totp_pin, name='crits-core-views-change_totp_pin'),
    url(r'^reset_password/$', views.reset_password, name='crits-core-views-reset_password'),
    url(r'^favorites/toggle/$', views.toggle_favorite, name='crits-core-views-toggle_favorite'),
    url(r'^favorites/view/$', views.favorites, name='crits-core-views-favorites'),
    url(r'^favorites/list/(?P<ctype>\S+)/(?P<option>\S+)/$', views.favorites_list, name='crits-core-views-favorites_list'),

    # User API Authentication
    url(r'^get_api_key/$', views.get_api_key, name='crits-core-views-get_api_key'),
    url(r'^create_api_key/$', views.create_api_key, name='crits-core-views-create_api_key'),
    url(r'^make_default_api_key/$', views.make_default_api_key, name='crits-core-views-make_default_api_key'),
    url(r'^revoke_api_key/$', views.revoke_api_key, name='crits-core-views-revoke_api_key'),

]
