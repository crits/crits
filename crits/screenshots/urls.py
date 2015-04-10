from django.conf.urls import patterns

urlpatterns = patterns('crits.screenshots.views',
    (r'^list/$', 'screenshots_listing'),
    (r'^list/(?P<option>\S+)/$', 'screenshots_listing'),
    (r'^add/$', 'add_new_screenshot'),
    (r'^find/$', 'find_screenshot'),
    (r'^remove_from_object/$', 'remove_screenshot_from_object'),
    (r'^render/(?P<_id>\S+)/(?P<thumb>\S+)/$', 'render_screenshot'),
    (r'^render/(?P<_id>\S+)/$', 'render_screenshot'),
    (r'^render/$', 'render_screenshot'),
)
