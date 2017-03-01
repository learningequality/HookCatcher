from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'^$', views.index, name ='index'),
    url(r'^state/$', views.allStates, name='allStates'),
	url(r'^state/(?P<gitSource>[a-zA-Z1-9]+)/(?P<gitSourceID>[a-zA-Z1-9:;_-]+)/$', views.singleState, name='singleState'),
    url(r'^diff/$', views.allDiffs, name='allDiffs'),
]   