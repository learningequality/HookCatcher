from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from . import views


urlpatterns = [
    url(r'^$', views.login, name='login'),
    url(r'^(?P<failed_attempt>True|False)/$', views.login, name='login'),

    url(r'^register/$', views.register, name='register'),

    # depricated paths
    url(r'^state/$', views.allStates, name='allStates'),
    url(r'^state/commit/(?P<gitCommitSHA>[a-zA-Z0-9]+)/$',
        views.singleCommit, name='singleCommit'),
    url(r'^state/branch/(?P<branchName>[a-zA-Z0-9:;_-]+)/(?P<commitSHA>[a-zA-Z1-9]+)/$',
        views.singleBranch, name='singleBranch'),
    url(r'^projects/(?P<repo_name>[a-zA-Z0-9%]+)/(?P<pr_number>[0-9]+)/$',
        views.singlePR, name='singlePR'),
    url(r'^projects/(?P<repo_name>[a-zA-Z0-9%]+)/(?P<pr_number>[0-9]+)/(?P<res_width>[0-9]+)/(?P<res_height>[0-9]+)/$',  # noqa: E501
        views.singlePR, name='singlePR'),

    # Internal APIs
    url(r'^api/register/$', views.api_register, name='api_register'),
    url(r'^api/login/$', views.api_login, name='api_login'),
    url(r'^api/test_websocket/$', views.test_websocket, name='test_websocket'),

    url(r'^api/logout/$', views.api_logout, name='api_logout'),
    url(r'^api/generate_diffs/(?P<repo_name>[a-zA-Z0-9%]+)/(?P<pr_number>[0-9]+)/(?P<base_commit>[a-zA-Z0-9]+)/(?P<head_commit>[a-zA-Z0-9]+)/$',  # noqa: E501
        views.api_generate_diffs, name='api_generate_diffs'),
    url(r'^webhook/$', views.webhook, name='webhook'),
    url(r'^bs_callback/(?P<img_id>[0-9]+)/$',
        views.browserstack_callback, name='browserstack_callback'),
    url(r'^approve_diff/$', views.approve_diff, name='approve_diff'),
    url(r'^approve_or_reset_diffs/$', views.approve_or_reset_diffs, name='approve_or_reset_diffs'),

    # Github OAuth handlers
    url(r'git_oauth_callback/$', views.git_oauth_callback, name='git_oauth_callback'),

    # Devon mockup paths
    url(r'^projects/$', views.projects, name='projects'),
    url(r'^projects/(?P<repo_name>[a-zA-Z0-9%]+)/$', views.listPR, name='listPR'),
    url(r'^projects/(?P<repo_name>[a-zA-Z0-9%]+)/pull/(?P<pr_number>[0-9]+)/$',
        views.view_pr, name='view_pr'),
    url(r'^projects/(?P<repo_name>[a-zA-Z0-9%]+)/pull/(?P<pr_number>[0-9]+)/history/$',
        views.pr_history, name='pr_history'),

]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
