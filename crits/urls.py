import imp
import os

from django.conf import settings
from django.conf.urls import include, url

urlpatterns = [

    url(r'^', include('crits.core.urls')),                        # Core
    url(r'^dashboards/', include('crits.dashboards.urls')),       # Dashboard
    url(r'^actors/', include('crits.actors.urls')),               # Actors
    url(r'^backdoors/', include('crits.backdoors.urls')),         # Backdoors
    url(r'^campaigns/', include('crits.campaigns.urls')),         # Campaigns
    url(r'^certificates/', include('crits.certificates.urls')),   # Certificates
    url(r'^comments/', include('crits.comments.urls')),           # Comments
    url(r'^domains/', include('crits.domains.urls')),             # Domains
    url(r'^emails/', include('crits.emails.urls')),               # Emails
    url(r'^events/', include('crits.events.urls')),               # Events
    url(r'^exploits/', include('crits.exploits.urls')),           # Exploits
    url(r'^indicators/', include('crits.indicators.urls')),       # Indicators
    url(r'^ips/', include('crits.ips.urls')),                     # IPs
    url(r'^locations/', include('crits.locations.urls')),         # Locations
    url(r'^notifications/', include('crits.notifications.urls')), # Notifications
    url(r'^objects/', include('crits.objects.urls')),             # Objects
    url(r'^pcaps/', include('crits.pcaps.urls')),                 # PCAPs
    url(r'^raw_data/', include('crits.raw_data.urls')),           # Raw Data
    url(r'^relationships/', include('crits.relationships.urls')), # Relationships
    url(r'^samples/', include('crits.samples.urls')),             # Samples
    url(r'^screenshots/', include('crits.screenshots.urls')),     # Screenshots
    url(r'^services/', include('crits.services.urls')),           # Services
    url(r'^signatures/', include('crits.signatures.urls')),       # Signatures
    url(r'^targets/', include('crits.targets.urls')),             # Targets
]

# Error overrides
handler500 = 'crits.core.errors.custom_500'
handler404 = 'crits.core.errors.custom_404'
handler403 = 'crits.core.errors.custom_403'
handler400 = 'crits.core.errors.custom_400'

# Enable the API if configured
# django_tastypie_mongoengine is broken with more recent versions of mongoengine
if settings.ENABLE_API:
    from tastypie.api import Api
    from crits.actors.api import ActorResource, ActorIdentifierResource
    from crits.backdoors.api import BackdoorResource
    from crits.campaigns.api import CampaignResource
    from crits.certificates.api import CertificateResource
    from crits.comments.api import CommentResource
    from crits.domains.api import DomainResource
    from crits.emails.api import EmailResource
    from crits.events.api import EventResource
    from crits.exploits.api import ExploitResource
    from crits.indicators.api import IndicatorResource, IndicatorActivityResource
    from crits.ips.api import IPResource
    from crits.pcaps.api import PCAPResource
    from crits.raw_data.api import RawDataResource
    from crits.samples.api import SampleResource
    from crits.screenshots.api import ScreenshotResource
    from crits.services.api import ServiceResource
    from crits.signatures.api import SignatureResource
    from crits.targets.api import TargetResource
    from crits.vocabulary.api import VocabResource

    v1_api = Api(api_name='v1')
    v1_api.register(ActorResource())
    v1_api.register(ActorIdentifierResource())
    v1_api.register(BackdoorResource())
    v1_api.register(CampaignResource())
    v1_api.register(CertificateResource())
    v1_api.register(CommentResource())
    v1_api.register(DomainResource())
    v1_api.register(EmailResource())
    v1_api.register(EventResource())
    v1_api.register(ExploitResource())
    v1_api.register(IndicatorResource())
    v1_api.register(IndicatorActivityResource())
    v1_api.register(IPResource())
    v1_api.register(PCAPResource())
    v1_api.register(RawDataResource())
    v1_api.register(SampleResource())
    v1_api.register(ScreenshotResource())
    v1_api.register(ServiceResource())
    v1_api.register(SignatureResource())
    v1_api.register(TargetResource())
    v1_api.register(VocabResource())

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

    urlpatterns.append(url(r'^api/', include(v1_api.urls)))

# This code allows static content to be served up by the development server
if settings.DEVEL_INSTANCE:
    from django.views.static import serve
    _media_url = settings.MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]
        urlpatterns.append(
            url(r'^%s(?P<path>.*)$' % _media_url, serve, {'document_root': settings.MEDIA_ROOT}))
    del(_media_url, serve)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
