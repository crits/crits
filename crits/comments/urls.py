from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^remove/(?P<obj_id>\S+)/$', views.remove_comment),
    url(r'^(?P<method>\S+)/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', views.add_update_comment),
    url(r'^activity/$', views.activity),
    url(r'^activity/(?P<atype>\S+)/(?P<value>\S+)/$', views.activity),
    url(r'^activity/get_new_comments/$', views.get_new_comments),
    url(r'^search/(?P<stype>[A-Za-z0-9\-\._]+)/(?P<sterm>.+?)/$', views.comment_search),
    url(r'^list/$', views.comments_listing),
    url(r'^list/(?P<option>\S+)/$', views.comments_listing),
]
