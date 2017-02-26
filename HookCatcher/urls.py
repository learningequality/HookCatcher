from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'^$', views.index, name ='index'),
	url(r'^PR/(?P<gitPRnumber>[0-9]+)/$', views.singlePR, name='singlePR'),
]