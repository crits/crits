from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^list/$', views.screenshots_listing),
    url(r'^list/(?P<option>\S+)/$', views.screenshots_listing),
    url(r'^add/$', views.add_new_screenshot),
    url(r'^find/$', views.find_screenshot),
    url(r'^remove_from_object/$', views.remove_screenshot_from_object),
    url(r'^render/(?P<_id>\S+)/(?P<thumb>\S+)/$', views.render_screenshot),
    url(r'^render/(?P<_id>\S+)/$', views.render_screenshot),
    url(r'^render/$', views.render_screenshot),
]
