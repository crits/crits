import imp
import os

from django.conf import settings
from django.conf.urls import include, patterns


urlpatterns = patterns('',

        # Core
        (r'^', include('crits.core.urls')),

        # Dashboard
        (r'^dashboards/', include('crits.dashboards.urls')),

        # Actors
        (r'^actors/', include('crits.actors.urls')),

        # Campaigns
        (r'^campaigns/', include('crits.campaigns.urls')),

        # Certificates
        (r'^certificates/', include('crits.certificates.urls')),

        # Comments
        (r'^comments/', include('crits.comments.urls')),

        # Disassembly
        (r'^disassembly/', include('crits.disassembly.urls')

        # Domains
        (r'^domains/', include('crits.domains.urls')),

        # Emails
        (r'^emails/', include('crits.emails.urls')),

        # Events
        (r'^events/', include('crits.events.urls')),

        # Indicators
        (r'^indicators/', include('crits.indicators.urls')),

        # IPs
        (r'^ips/', include('crits.ips.urls')),

        # Objects
        (r'^objects/', include('crits.objects.urls')),

        # PCAPs
        (r'^pcaps/', include('crits.pcaps.urls')),

        # Raw Data
        (r'^raw_data/', include('crits.raw_data.urls')),

        # Relationships
        (r'^relationships/', include('crits.relationships.urls')),

        # Samples
        (r'^samples/', include('crits.samples.urls')),

        # Screenshots
        (r'^screenshots/', include('crits.screenshots.urls')),

        # Services
        (r'^services/', include('crits.services.urls')),

        # Standards
        (r'^standards/', include('crits.standards.urls')),

        # Targets
        (r'^targets/', include('crits.targets.urls')),
)

# Enable the API if configured
if settings.ENABLE_API:
    from tastypie.api import Api
    from crits.actors.api import ActorResource, ActorIdentifierResource
    from crits.campaigns.api import CampaignResource
    from crits.certificates.api import CertificateResource
    from crits.disassembly.api import DisassemblyResource
    from crits.domains.api import DomainResource, WhoIsResource
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
    from crits.standards.api import StandardsResource

    v1_api = Api(api_name='v1')
    v1_api.register(ActorResource())
    v1_api.register(ActorIdentifierResource())
    v1_api.register(CampaignResource())
    v1_api.register(CertificateResource())
    v1_api.register(DisassemblyResource())
    v1_api.register(DomainResource())
    v1_api.register(WhoIsResource())
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
    v1_api.register(StandardsResource())

    for service_directory in settings.SERVICE_DIRS:
        if os.path.isdir(service_directory):
            for d in os.listdir(service_directory):
                abs_path = os.path.join(service_directory, d, 'urls.py')
                if os.path.isfile(abs_path):
                    try:
                        rdef = imp.load_source('urls', abs_path)
                        rdef.register_api(v1_api)
                    except Exception, e:
                        pass

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
