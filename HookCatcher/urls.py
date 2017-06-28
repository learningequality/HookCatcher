from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^state/$', views.allStates, name='allStates'),

    url(r'^(?P<gitRepo>[a-zA-Z0-9/]+)/compare/$', views.listPR, name='listPR'),

    url(r'^compare/$', views.listPR, name='listPR'),

    url(r'^compare/(?P<prNumber>[0-9]+)/$', views.singlePR, name='singlePR'),
    url(r'^compare/(?P<prNumber>[0-9]+)/(?P<resWidth>[0-9]+)/(?P<resHeight>[0-9]+)$',
        views.singlePR, name='singlePR'),

    url(r'^state/commit/(?P<gitCommitSHA>[a-zA-Z0-9]+)/$',
        views.singleCommit, name='singleCommit'),
    url(r'^state/branch/(?P<branchName>[a-zA-Z0-9:;_-]+)/(?P<commitSHA>[a-zA-Z1-9]+)/$',
        views.singleBranch, name='singleBranch'),
    url(r'^img/(?P<imageID>.*)/$',
        views.getImage, name='getImage'),
    url(r'^webhook/$', views.webhook, name='webhook'),
]
