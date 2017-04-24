from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^state/$', views.allStates, name='allStates'),
    url(r'^state/branch/(?P<branchName>[a-zA-Z1-9:;_-]+)/(?P<commitSHA>[a-zA-Z1-9]+)/$',
        views.singleBranch, name='singleBranch'),
    url(r'^state/pr/(?P<prNumber>[1-9]+)/(?P<commitSHA>[a-zA-Z1-9]+)/$',
        views.singlePR, name='singlePR'),
    url(r'^img/(?P<imageID>.*)/$',
        views.getImage, name='getImage'),
    url(r'^webhook/$', views.webhook, name='webhook'),
]
