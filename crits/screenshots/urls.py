from django.conf.urls import url

urlpatterns = [
    url(r'^list/$', 'screenshots_listing', prefix='crits.screenshots.views'),
    url(r'^list/(?P<option>\S+)/$', 'screenshots_listing', prefix='crits.screenshots.views'),
    url(r'^add/$', 'add_new_screenshot', prefix='crits.screenshots.views'),
    url(r'^find/$', 'find_screenshot', prefix='crits.screenshots.views'),
    url(r'^remove_from_object/$', 'remove_screenshot_from_object', prefix='crits.screenshots.views'),
    url(r'^render/(?P<_id>\S+)/(?P<thumb>\S+)/$', 'render_screenshot', prefix='crits.screenshots.views'),
    url(r'^render/(?P<_id>\S+)/$', 'render_screenshot', prefix='crits.screenshots.views'),
    url(r'^render/$', 'render_screenshot', prefix='crits.screenshots.views'),
]
