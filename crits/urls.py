from django.contrib.auth.views import logout_then_login
from django.conf import settings
from django.conf.urls import include, patterns


urlpatterns = patterns('',

        # authentication
        (r'^login/$', 'crits.core.views.login'),
        (r'^logout/$', logout_then_login),

        # api
        (r'^get_api_key/$', 'crits.core.views.get_api_key'),
        (r'^create_api_key/$', 'crits.core.views.create_api_key'),
        (r'^revoke_api_key/$', 'crits.core.views.revoke_api_key'),

        #core
        (r'^status/update/(?P<type_>\S+)/(?P<id_>\S+)/$', 'crits.core.views.update_status'),
        (r'^search/$', 'crits.core.views.global_search_listing'),
        (r'^$', 'crits.core.views.dashboard'),
        (r'^about/$', 'crits.core.views.about'),
        (r'^help/$', 'crits.core.views.help'),
        (r'^dashboard/$', 'crits.core.views.dashboard'),
        (r'^profile/(?P<user>\S+)/$', 'crits.core.views.profile'),
        (r'^profile/$', 'crits.core.views.profile'),
        (r'^details/(?P<type_>\S+)/(?P<id_>\S+)/$', 'crits.core.views.details'),
        (r'^source_access/$', 'crits.core.views.source_access'),
        (r'^timeline/(?P<data_type>\S+)/$', 'crits.core.views.timeline'),
        (r'^timeline/(?P<data_type>\S+)/(?P<extra_data>\S+)/$', 'crits.core.views.timeline'),
        (r'^timeline/$', 'crits.core.views.timeline'),
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
        (r'^object/download/$', 'crits.core.views.download_object'),
        (r'^files/download/(?P<sample_md5>\w+)/$', 'crits.core.views.download_file'),
        (r'^object/sources/removeall/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', 'crits.core.views.remove_all_source'),
        (r'^object/sources/remove/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', 'crits.core.views.remove_source'),
        (r'^object/sources/(?P<method>\S+)/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', 'crits.core.views.add_update_source'),
        (r'^source_releasability/$', 'crits.core.views.source_releasability'),
        (r'^bucket/list/$', 'crits.core.views.bucket_list'),
        (r'^bucket/list/(?P<option>.+)$', 'crits.core.views.bucket_list'),
        (r'^bucket/mod/$', 'crits.core.views.bucket_modify'),
        (r'^bucket/promote/$', 'crits.core.views.bucket_promote'),
        (r'^counts/list/$', 'crits.core.views.counts_listing'),
        (r'^counts/list/(?P<option>\S+)/$', 'crits.core.views.counts_listing'),
        (r'^config/$', 'crits.config.views.crits_config'),
        (r'^modify_config/$', 'crits.config.views.modify_config'),
        (r'^change_password/$', 'crits.core.views.change_password'),
        (r'^change_totp_pin/$', 'crits.core.views.change_totp_pin'),
        (r'^control_panel/$', 'crits.core.views.control_panel'),
        (r'^audit/list/$', 'crits.core.views.audit_listing'),
        (r'^audit/list/(?P<option>\S+)/$', 'crits.core.views.audit_listing'),
        (r'^items/editor/$', 'crits.core.views.item_editor'),
        (r'^items/list/$', 'crits.core.views.items_listing'),
        (r'^items/list/(?P<itype>\S+)/(?P<option>\S+)/$', 'crits.core.views.items_listing'),
        (r'^items/toggle_active/$', 'crits.core.views.toggle_item_active'),
        (r'^users/toggle_active/$', 'crits.core.views.toggle_user_active'),
        (r'^users/list/$', 'crits.core.views.users_listing'),
        (r'^users/list/(?P<option>\S+)/$', 'crits.core.views.users_listing'),
        (r'^reset_password/$', 'crits.core.views.reset_password'),
        (r'^get_item_data/$', 'crits.core.views.get_item_data'),
        (r'^get_dialog/(?P<dialog>[A-Za-z0-9\-\._-]+)$', 'crits.core.views.get_dialog'),
        (r'^get_dialog/$', 'crits.core.views.get_dialog'),
        (r'^tickets/(?P<method>\S+)/(?P<type_>\w+)/(?P<id_>\w+)/$', 'crits.core.views.add_update_ticket'),
        (r'^get_search_help/$', 'crits.core.views.get_search_help'),
        (r'^favorites/toggle/$', 'crits.core.views.toggle_favorite'),
        (r'^favorites/view/$', 'crits.core.views.favorites'),
        (r'^favorites/list/(?P<ctype>\S+)/(?P<option>\S+)/$', 'crits.core.views.favorites_list'),


        #campaigns
        (r'^campaigns/stats/$', 'crits.campaigns.views.campaign_stats'),
        (r'^campaigns/list/$', 'crits.campaigns.views.campaigns_listing'),
        (r'^campaigns/list/(?P<option>\S+)/$', 'crits.campaigns.views.campaigns_listing'),
        (r'^campaigns/details/(?P<campaign_name>.+?)/$', 'crits.campaigns.views.campaign_details'),
        (r'^campaigns/add/(?P<ctype>\w+)/(?P<objectid>\w+)/$', 'crits.campaigns.views.campaign_add'),
        (r'^campaigns/new/$', 'crits.campaigns.views.add_campaign'),
        (r'^campaigns/remove/(?P<ctype>\w+)/(?P<objectid>\w+)/$', 'crits.campaigns.views.remove_campaign'),
        (r'^campaigns/edit/(?P<ctype>\w+)/(?P<objectid>\w+)/$', 'crits.campaigns.views.edit_campaign'),
        (r'^campaigns/ttp/(?P<cid>\w+)/$', 'crits.campaigns.views.campaign_ttp'),
        (r'^campaigns/set_description/(?P<name>.+?)/$', 'crits.campaigns.views.set_campaign_description'),
        (r'^campaigns/aliases/$', 'crits.campaigns.views.campaign_aliases'),

        #certificates
        (r'^certificates/details/(?P<md5>\w+)/$', 'crits.certificates.views.certificate_details'),
        (r'^certificates/set_description/(?P<md5>\w+)/$', 'crits.certificates.views.set_certificate_description'),
        (r'^certificates/upload/$', 'crits.certificates.views.upload_certificate'),
        (r'^certificates/remove/(?P<md5>[\S ]+)$', 'crits.certificates.views.remove_certificate'),
        (r'^certificates/list/$', 'crits.certificates.views.certificates_listing'),
        (r'^certificates/list/(?P<option>\S+)/$', 'crits.certificates.views.certificates_listing'),


        #comments
        (r'^comments/remove/(?P<obj_id>\S+)/$', 'crits.comments.views.remove_comment'),
        (r'^comments/(?P<method>\S+)/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', 'crits.comments.views.add_update_comment'),
        (r'^activity/$', 'crits.comments.views.activity'),
        (r'^activity/(?P<atype>\S+)/(?P<value>\S+)/$', 'crits.comments.views.activity'),
        (r'^activity/get_new_comments/$', 'crits.comments.views.get_new_comments'),
        (r'^comments/search/(?P<stype>[A-Za-z0-9\-\._]+)/(?P<sterm>.+?)/$', 'crits.comments.views.comment_search'),
        (r'^comments/list/$', 'crits.comments.views.comments_listing'),
        (r'^comments/list/(?P<option>\S+)/$', 'crits.comments.views.comments_listing'),

        #domains
        (r'^domains/list/$', 'crits.domains.views.domains_listing'),
        (r'^domains/list/(?P<option>\S+)/$', 'crits.domains.views.domains_listing'),
        (r'^domains/tld_update/$', 'crits.domains.views.tld_update'),
        (r'^domains/details/(?P<domain>\S+)/$', 'crits.domains.views.domain_detail'),
        (r'^domains/search/$', 'crits.domains.views.domain_search'),
        (r'^domains/add/$', 'crits.domains.views.add_domain'),
        (r'^domains/bulkadd/$', 'crits.domains.views.bulk_add_domain'),
        (r'^domains/edit/(?P<domain>\S+)/$', 'crits.domains.views.edit_domain'),
        (r'^domains/update_whois/(?P<domain>\S+)/$', 'crits.domains.views.update_whois'),

        #emails
        (r'^emails/search/$', 'crits.emails.views.email_search'),
        (r'^emails/delete/(?P<email_id>\w+)/$', 'crits.emails.views.email_del'),
        (r'^emails/upload/attach/(?P<email_id>\w+)/$', 'crits.emails.views.upload_attach'),
        (r'^emails/details/(?P<email_id>\w+)/$', 'crits.emails.views.email_detail'),
        (r'^emails/new/fields/$', 'crits.emails.views.email_fields_add'),
        (r'^emails/new/outlook/$', 'crits.emails.views.email_outlook_add'),
        (r'^emails/new/raw/$', 'crits.emails.views.email_raw_add'),
        (r'^emails/new/yaml/$', 'crits.emails.views.email_yaml_add'),
        (r'^emails/new/eml/$', 'crits.emails.views.email_eml_add'),
        (r'^emails/edit/(?P<email_id>\w+)/$', 'crits.emails.views.email_yaml_add'),
        (r'^emails/get_cybox/(?P<email_id>\w+)/$', 'crits.emails.views.get_email_cybox'),
        (r'^emails/update_header_value/(?P<email_id>\w+)/$', 'crits.emails.views.update_header_value'),
        (r'^emails/indicator_from_header_field/(?P<email_id>\w+)/$', 'crits.emails.views.indicator_from_header_field'),
        (r'^emails/list/$', 'crits.emails.views.emails_listing'),
        (r'^emails/list/(?P<option>\S+)/$', 'crits.emails.views.emails_listing'),

        #events
        (r'^events/details/(?P<eventid>\w+)/$', 'crits.events.views.view_event'),
        (r'^events/add/$', 'crits.events.views.add_event'),
        (r'^events/search/$', 'crits.events.views.event_search'),
        (r'^events/upload/sample/(?P<event_id>\w+)/$', 'crits.events.views.upload_sample'),
        (r'^events/remove/(?P<_id>[\S ]+)$', 'crits.events.views.remove_event'),
        (r'^events/set_description/(?P<event_id>\w+)/$', 'crits.events.views.set_event_description'),
        (r'^events/set_title/(?P<event_id>\w+)/$', 'crits.events.views.set_event_title'),
        (r'^events/set_type/(?P<event_id>\w+)/$', 'crits.events.views.set_event_type'),
        (r'^events/get_event_types/$', 'crits.events.views.get_event_type_dropdown'),
        (r'^events/list/$', 'crits.events.views.events_listing'),
        (r'^events/list/(?P<option>\S+)/$', 'crits.events.views.events_listing'),


        #indicators
        (r'^indicators/details/(?P<indicator_id>\w+)/$', 'crits.indicators.views.indicator'),
        (r'^indicators/search/$', 'crits.indicators.views.indicator_search'),
        (r'^indicators/upload/$', 'crits.indicators.views.upload_indicator'),
        (r'^indicators/add_action/$', 'crits.indicators.views.new_indicator_action'),
        (r'^indicators/remove/(?P<_id>[\S ]+)$', 'crits.indicators.views.remove_indicator'),
        (r'^indicators/action/remove/(?P<indicator_id>\w+)/$', 'crits.indicators.views.remove_action'),
        (r'^indicators/activity/remove/(?P<indicator_id>\w+)/$', 'crits.indicators.views.remove_activity'),
        (r'^indicators/actions/(?P<method>\S+)/(?P<indicator_id>\w+)/$', 'crits.indicators.views.add_update_action'),
        (r'^indicators/activity/(?P<method>\S+)/(?P<indicator_id>\w+)/$', 'crits.indicators.views.add_update_activity'),
        (r'^indicators/ci/update/(?P<indicator_id>\w+)/(?P<ci_type>\S+)/$', 'crits.indicators.views.update_ci'),
        (r'^indicators/type/update/(?P<indicator_id>\w+)/$', 'crits.indicators.views.update_indicator_type'),
        (r'^indicators/and_ip/$', 'crits.indicators.views.indicator_and_ip'),
        (r'^indicators/from_raw/$', 'crits.indicators.views.indicator_from_raw'),
        (r'^indicators/list/$', 'crits.indicators.views.indicators_listing'),
        (r'^indicators/list/(?P<option>\S+)/$', 'crits.indicators.views.indicators_listing'),

        #ips
        (r'^ips/search/$', 'crits.ips.views.ip_search'),
        (r'^ips/search/(?P<ip_str>\S+)/$', 'crits.ips.views.ip_search'),
        (r'^ips/details/(?P<ip>\S+)/$', 'crits.ips.views.ip_detail'),
        (r'^ips/remove/$', 'crits.ips.views.remove_ip'),
        (r'^ips/list/$', 'crits.ips.views.ips_listing'),
        (r'^ips/list/(?P<option>\S+)/$', 'crits.ips.views.ips_listing'),
        (r'^ips/bulkadd/$', 'crits.ips.views.bulk_add_ip'),
        (r'^ips/(?P<method>\S+)/$', 'crits.ips.views.add_update_ip'),


        #objects
        (r'^objects/add/$', 'crits.objects.views.add_new_object'),
        (r'^objects/delete/$', 'crits.objects.views.delete_this_object'),
        (r'^objects/get_dropdown/$', 'crits.objects.views.get_object_type_dropdown'),
        (r'^objects/update_objects_value/$', 'crits.objects.views.update_objects_value'),
        (r'^objects/update_objects_source/$', 'crits.objects.views.update_objects_source'),
        (r'^objects/create_indicator/$', 'crits.objects.views.indicator_from_object'),
        (r'^objects/bulkadd/$', 'crits.objects.views.bulk_add_object'),
        (r'^objects/bulkaddinline/$', 'crits.objects.views.bulk_add_object_inline'),

        #pcaps
        (r'^pcaps/details/(?P<md5>\w+)/$', 'crits.pcaps.views.pcap_details'),
        (r'^pcaps/set_description/(?P<md5>\w+)/$', 'crits.pcaps.views.set_pcap_description'),
        (r'^pcaps/upload/$', 'crits.pcaps.views.upload_pcap'),
        (r'^pcaps/remove/(?P<md5>[\S ]+)$', 'crits.pcaps.views.remove_pcap'),
        (r'^pcaps/list/$', 'crits.pcaps.views.pcaps_listing'),
        (r'^pcaps/list/(?P<option>\S+)/$', 'crits.pcaps.views.pcaps_listing'),

        #raw_data
        (r'^raw_data/details/(?P<_id>\w+)/$', 'crits.raw_data.views.raw_data_details'),
        (r'^raw_data/details_by_link/(?P<link>.+)/$', 'crits.raw_data.views.details_by_link'),
        (r'^raw_data/get_inline_comments/(?P<_id>\w+)/$', 'crits.raw_data.views.get_inline_comments'),
        (r'^raw_data/get_versions/(?P<_id>\w+)/$', 'crits.raw_data.views.get_raw_data_versions'),
        (r'^raw_data/set_description/(?P<_id>\w+)/$', 'crits.raw_data.views.set_raw_data_description'),
        (r'^raw_data/set_tool_details/(?P<_id>\w+)/$', 'crits.raw_data.views.set_raw_data_tool_details'),
        (r'^raw_data/set_tool_name/(?P<_id>\w+)/$', 'crits.raw_data.views.set_raw_data_tool_name'),
        (r'^raw_data/set_raw_data_type/(?P<_id>\w+)/$', 'crits.raw_data.views.set_raw_data_type'),
        (r'^raw_data/set_raw_data_highlight_comment/(?P<_id>\w+)/$', 'crits.raw_data.views.set_raw_data_highlight_comment'),
        (r'^raw_data/set_raw_data_highlight_date/(?P<_id>\w+)/$', 'crits.raw_data.views.set_raw_data_highlight_date'),
        (r'^raw_data/add_inline_comment/(?P<_id>\w+)/$', 'crits.raw_data.views.add_inline_comment'),
        (r'^raw_data/add_highlight/(?P<_id>\w+)/$', 'crits.raw_data.views.add_highlight'),
        (r'^raw_data/remove_highlight/(?P<_id>\w+)/$', 'crits.raw_data.views.remove_highlight'),
        (r'^raw_data/upload/(?P<link_id>.+)/$', 'crits.raw_data.views.upload_raw_data'),
        (r'^raw_data/upload/$', 'crits.raw_data.views.upload_raw_data'),
        (r'^raw_data/remove/(?P<_id>[\S ]+)$', 'crits.raw_data.views.remove_raw_data'),
        (r'^raw_data/list/$', 'crits.raw_data.views.raw_data_listing'),
        (r'^raw_data/list/(?P<option>\S+)/$', 'crits.raw_data.views.raw_data_listing'),
        (r'^raw_data/add_data_type/$', 'crits.raw_data.views.new_raw_data_type'),
        (r'^raw_data/get_data_types/$', 'crits.raw_data.views.get_raw_data_type_dropdown'),


        #relationships
        (r'^relationships/forge/$', 'crits.relationships.views.add_new_relationship'),
        (r'^relationships/breakup/$', 'crits.relationships.views.break_relationship'),
        (r'^relationships/get_dropdown/$', 'crits.relationships.views.get_relationship_type_dropdown'),
        (r'^relationships/update_relationship_type/$', 'crits.relationships.views.update_relationship_type'),
        (r'^relationships/update_relationship_date/$', 'crits.relationships.views.update_relationship_date'),

        #samples
        (r'^samples/upload/$', 'crits.samples.views.upload_file'),
        (r'^samples/upload_child/(?P<parent_md5>\w+)/$', 'crits.samples.views.upload_child'),
        (r'^samples/upload_list/(?P<filename>[\S ]+)/(?P<md5s>.+)/$', 'crits.samples.views.view_upload_list'),
        (r'^samples/bulkadd/$', 'crits.samples.views.bulk_add_md5_sample'),
        (r'^samples/details/(?P<sample_md5>\w+)/$', 'crits.samples.views.detail'),
        (r'^samples/strings/(?P<sample_md5>\w+)/$', 'crits.samples.views.strings'),
        (r'^samples/stackstrings/(?P<sample_md5>\w+)/$', 'crits.samples.views.stackstrings'),
        (r'^samples/hex/(?P<sample_md5>\w+)/$', 'crits.samples.views.hex'),
        (r'^samples/xor/(?P<sample_md5>\w+)/$', 'crits.samples.views.xor'),
        (r'^samples/xor_searcher/(?P<sample_md5>\w+)/$', 'crits.samples.views.xor_searcher'),
        (r'^samples/unrar/(?P<md5>\w+)/$', 'crits.samples.views.unrar_sample'),
        (r'^samples/unzip/(?P<md5>\w+)/$', 'crits.samples.views.unzip_sample'),
        (r'^samples/sources/$', 'crits.samples.views.sources'),
        (r'^samples/exploits/$', 'crits.samples.views.exploit'),
        (r'^samples/new/exploit/$', 'crits.samples.views.new_exploit'),
        (r'^samples/new/backdoor/$', 'crits.samples.views.new_backdoor'),
        (r'^samples/add/backdoor/(?P<sample_md5>\w+)/$', 'crits.samples.views.add_backdoor'),
        (r'^samples/add/exploit/(?P<sample_md5>\w+)/$', 'crits.samples.views.add_exploit'),
        (r'^samples/remove/(?P<md5>[\S ]+)$', 'crits.samples.views.remove_sample'),
        (r'^samples/list/$', 'crits.samples.views.samples_listing'),
        (r'^samples/list/(?P<option>\S+)/$', 'crits.samples.views.samples_listing'),
        (r'^samples/backdoors/list/$', 'crits.samples.views.backdoors_listing'),
        (r'^samples/backdoors/list/(?P<option>\S+)/$', 'crits.samples.views.backdoors_listing'),
        (r'^samples/yarahits/list/$', 'crits.samples.views.yarahits_listing'),
        (r'^samples/yarahits/list/(?P<option>\S+)/$', 'crits.samples.views.yarahits_listing'),

        # Screenshots
        (r'^screenshots/list/$', 'crits.screenshots.views.screenshots_listing'),
        (r'^screenshots/list/(?P<option>\S+)/$', 'crits.screenshots.views.screenshots_listing'),
        (r'^screenshots/add/$', 'crits.screenshots.views.add_new_screenshot'),
        (r'^screenshots/edit_description/$', 'crits.screenshots.views.update_ss_description'),
        (r'^screenshots/find/$', 'crits.screenshots.views.find_screenshot'),
        (r'^screenshots/remove_from_object/$', 'crits.screenshots.views.remove_screenshot_from_object'),
        (r'^screenshots/render/(?P<_id>\S+)/(?P<thumb>\S+)/$', 'crits.screenshots.views.render_screenshot'),
        (r'^screenshots/render/(?P<_id>\S+)/$', 'crits.screenshots.views.render_screenshot'),
        (r'^screenshots/render/$', 'crits.screenshots.views.render_screenshot'),

        # Services
        (r'^services/', include('crits.services.urls')),

        # Standards
        (r'^standards/upload/$', 'crits.standards.views.upload_standards'),

        #targets
        (r'^targets/list/$', 'crits.targets.views.targets_listing'),
        (r'^targets/list/(?P<option>\S+)/$', 'crits.targets.views.targets_listing'),
        (r'^targets/divisions/list/$', 'crits.targets.views.divisions_listing'),
        (r'^targets/divisions/list/(?P<option>\S+)/$', 'crits.targets.views.divisions_listing'),
        (r'^targets/add_target/$', 'crits.targets.views.add_update_target'),
        (r'^targets/details/(?P<email_address>[\S ]+)/$', 'crits.targets.views.target_details'),
        (r'^targets/details/$', 'crits.targets.views.target_details'),
        (r'^targets/info/(?P<email_address>[\S ]+)/$', 'crits.targets.views.target_info'),
)

# Enable the API if configured
if settings.ENABLE_API:
    from tastypie.api import Api
    from crits.campaigns.api import CampaignResource
    from crits.certificates.api import CertificateResource
    from crits.domains.api import DomainResource
    from crits.emails.api import EmailResource
    from crits.events.api import EventResource
    from crits.indicators.api import IndicatorResource, IndicatorActivityResource
    from crits.ips.api import IPResource
    from crits.objects.api import ObjectResource
    from crits.pcaps.api import PCAPResource
    from crits.raw_data.api import RawDataResource
    from crits.relationships.api import RelationshipResource
    from crits.samples.api import SampleResource
    from crits.screenshots.api import ScreenshotResource
    from crits.services.api import ServiceResource
    from crits.targets.api import TargetResource

    v1_api = Api(api_name='v1')
    v1_api.register(CampaignResource())
    v1_api.register(CertificateResource())
    v1_api.register(DomainResource())
    v1_api.register(EmailResource())
    v1_api.register(EventResource())
    v1_api.register(IndicatorResource())
    v1_api.register(IndicatorActivityResource())
    v1_api.register(IPResource())
    v1_api.register(ObjectResource())
    v1_api.register(PCAPResource())
    v1_api.register(RawDataResource())
    v1_api.register(RelationshipResource())
    v1_api.register(SampleResource())
    v1_api.register(ScreenshotResource())
    v1_api.register(ServiceResource())
    v1_api.register(TargetResource())

    urlpatterns += patterns('',
        (r'^api/', include(v1_api.urls)),
    )

# This code allows static content to be served up by the development server
if settings.DEVEL_INSTANCE:
    from django.views.static import serve
    _media_url = settings.MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]
        urlpatterns += patterns('',
                (r'^%s(?P<path>.*)$' % _media_url, serve, {'document_root': settings.MEDIA_ROOT}))
    del(_media_url, serve)
