from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from . import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^state/$', views.allStates, name='allStates'),

    url(r'^(?P<git_repo>[a-zA-Z0-9/]+)/compare/$', views.listPR, name='listPR'),

    url(r'^compare/$', views.listPR, name='listPR'),

    url(r'^compare/(?P<pr_number>[0-9]+)/$', views.singlePR, name='singlePR'),
    url(r'^compare/(?P<pr_number>[0-9]+)/(?P<res_width>[0-9]+)/(?P<res_height>[0-9]+)$',
        views.singlePR, name='singlePR'),

    url(r'^state/commit/(?P<gitCommitSHA>[a-zA-Z0-9]+)/$',
        views.singleCommit, name='singleCommit'),
    url(r'^state/branch/(?P<branchName>[a-zA-Z0-9:;_-]+)/(?P<commitSHA>[a-zA-Z1-9]+)/$',
        views.singleBranch, name='singleBranch'),
    url(r'^webhook/$', views.webhook, name='webhook'),
    url(r'^bs_callback/(?P<img_id>[0-9]+)$', views.browserstack_callback, name='browserstack_callback'),
]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)