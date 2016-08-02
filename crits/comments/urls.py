from django.conf.urls import url

urlpatterns = [
    url(r'^remove/(?P<obj_id>\S+)/$', 'remove_comment', prefix='crits.comments.views'),
    url(r'^(?P<method>\S+)/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', 'add_update_comment', prefix='crits.comments.views'),
    url(r'^activity/$', 'activity', prefix='crits.comments.views'),
    url(r'^activity/(?P<atype>\S+)/(?P<value>\S+)/$', 'activity', prefix='crits.comments.views'),
    url(r'^activity/get_new_comments/$', 'get_new_comments', prefix='crits.comments.views'),
    url(r'^search/(?P<stype>[A-Za-z0-9\-\._]+)/(?P<sterm>.+?)/$', 'comment_search', prefix='crits.comments.views'),
    url(r'^list/$', 'comments_listing', prefix='crits.comments.views'),
    url(r'^list/(?P<option>\S+)/$', 'comments_listing', prefix='crits.comments.views'),
]
