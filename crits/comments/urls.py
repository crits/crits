from django.conf.urls import patterns

urlpatterns = patterns('crits.comments.views',
    (r'^remove/(?P<obj_id>\S+)/$', 'remove_comment'),
    (r'^(?P<method>\S+)/(?P<obj_type>\S+)/(?P<obj_id>\S+)/$', 'add_update_comment'),
    (r'^activity/$', 'activity'),
    (r'^activity/(?P<atype>\S+)/(?P<value>\S+)/$', 'activity'),
    (r'^activity/get_new_comments/$', 'get_new_comments'),
    (r'^search/(?P<stype>[A-Za-z0-9\-\._]+)/(?P<sterm>.+?)/$', 'comment_search'),
    (r'^list/$', 'comments_listing'),
    (r'^list/(?P<option>\S+)/$', 'comments_listing'),
)
