import json
import os
import urllib

import django_rq
import requests

from django.conf import settings  # database dir
from django.contrib.auth import login as login_auth
from django.contrib.auth import logout as logout_auth
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.management import call_command  # call newPR update command
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from HookCatcher.management.commands.functions.gen_diff import gen_diff

from .models import PR, Commit, Diff, History, Image, Profile, State


# representation for models so you don't have to change every value for models in every template
def commit_representation(commit_obj):
    return {
        'git_repo': commit_obj.git_repo,
        'git_branch': commit_obj.git_branch,
        'git_hash': commit_obj.git_hash
    }


# store all info about a state into one object
def state_representation(state_obj):
    return {
        'name': state_obj.state_name,
        'desc': state_obj.state_desc,
        'url': state_obj.full_url,
        'git_repo': state_obj.git_commit.git_repo,
        'git_branch': state_obj.git_commit.git_branch,
        'git_commit_sha': state_obj.git_commit.git_hash,
        'imgs_of_state': state_obj.image_set.all()
    }


def pr_representation(pr_obj):
    return {
        'git_repo': pr_obj.git_repo,
        'git_pr_number': pr_obj.git_pr_number,
        'git_target_commit': commit_representation(pr_obj.git_target_commit),
        'git_source_commit': commit_representation(pr_obj.git_source_commit),
    }


def image_representation(image_obj):
    img_name = image_obj.get_image_location()
    return {
        'name': img_name,
        'browser_type': image_obj.browser_type,
        'operating_system': image_obj.operating_system,
        'width': image_obj.device_res_width,
        'height': image_obj.device_res_height,
        'state': state_representation(image_obj.state)
    }


def diff_representation(diff_obj):
    return {
        'name': os.path.join(settings.MEDIA_URL, diff_obj.diff_img_file.name),
        'target_img': image_representation(diff_obj.target_img),
        'source_img': image_representation(diff_obj.source_img),
        'diff_percent': diff_obj.diff_percent
    }


# only take the information needed from JSON response
def gitCommitRepresentation(git_info):
    return {
        'url': git_info['html_url'],
        'author': git_info['commit']['author']['name'],
        'date': git_info['commit']['author']['date'],
        'filesChanged': len(git_info['files'])
    }


# retrieve all states with a matching PR number
def singleCommit(request, gitCommitSHA):
    commitObj = Commit.objects.filter(gitHash=gitCommitSHA)
    states = State.objects.get(gitCommit=commitObj)

    formattedStates = [state_representation(state) for state in states]

    gitInfo = gitCommitInfo(commitObj.gitHash)
    return render(request, 'state/detail.html', {
        'statesList': formattedStates,
        'gitCommit': gitInfo,
    })


# retrieve all states from State model
def allStates(request):
    allStates = State.objects.all()
    formattedStates = [state_representation(state) for state in allStates]
    return render(request, 'state/index.html', {
        'statesList': formattedStates,
    })


# get request to github API
def gitCommitInfo(gitSHA):
    GIT_HEADER = {
        'Authorization': 'token ' + settings.GIT_OAUTH,
    }

    GIT_REPO_API = 'https://api.github.com/repos/{0}'.format(settings.GIT_REPO)

    # ex. commit url = https://github.com/MingDai/kolibri/pull/6/commits/
    gitRepoURL = os.path.join(GIT_REPO_API, 'commits')
    gitCommitURL = os.path.join(gitRepoURL, gitSHA)
    getCommit = requests.get(gitCommitURL, headers=GIT_HEADER)

    if(getCommit.status_code == 200):
        gitCommitObj = json.loads(getCommit.text)
        return gitCommitRepresentation(gitCommitObj)


def login(request, failed_attempt=False):
    if failed_attempt == 'False':
        failed_attempt = False
    return render(request, 'login.html', {
            'failed_attempt': failed_attempt,
    })


def register(request):
    return render(request, 'register.html')


'''
    Function to retrieve relevant info from Github
    get a list of repositories that correspond to a particular git Profile

    To get all pull requests use ?access_token for private repos
    "pulls_url": "https://api.github.com/repos/MingDai/gittest/pulls{/number}"

    To get all branches of a repo use ?access_token for private repos
    "branches_url": "https://api.github.com/repos/MingDai/gittest/branches{/branch}"
    NEED SOME PERMISSIONS IDONO WHICH
'''


def git_list_repositories(git_access_token):
    integration_repos = []

    # custom header
    # https://developer.github.com/apps/building-integrations/setting-up-and-registering-github-apps/identifying-users-for-github-apps/  # noqa: E501
    git_header = {
        'Accept': 'application/vnd.github.machine-man-preview+json',
    }

    # get all the integration ids
    installs_url = 'https://api.github.com/user/installations'

    get_installs = requests.get('{0}?access_token={1}'.format(installs_url, git_access_token),
                                headers=git_header)
    installs = json.loads(get_installs.text)

    for installation in installs['integration_installations']:
        # get all the repos for this particular integration
        user_repos_url = "{0}/{1}/repositories?access_token={2}".format(installs_url,
                                                                        installation['id'],
                                                                        git_access_token)
        get_repos = requests.get(user_repos_url, headers=git_header)
        all_repos = json.loads(get_repos.text)
        for repo in all_repos['repositories']:
            integration_repos.append(repo['full_name'])  # "MingDai/HookCatcher"

    return integration_repos


def projects(request):
    if request.user.is_authenticated:
        unique_repos = Commit.objects.order_by().values('git_repo').distinct()
        # unique_repos = git_list_repositories(request.user.profile.git_access_token)
        return render(request, 'projects/index.html', {
            'repoList': unique_repos,
        })
    else:
        return redirect('login')


def listPR(request, repo_name):
    repo_name = urllib.unquote(repo_name)
    pr_list = PR.objects.filter(git_repo=repo_name).order_by('-git_pr_number')

    return render(request, 'compare/index.html', {
        'prList': pr_list,
        'gitRepo': repo_name
    })


# DEPRECATED
# retrieve all states with a matching branch name
def singleBranch(request, branch_name, commitSHA):
    branch_states = State.objects.filter(git_branch=branch_name)
    formatted_states = [state_representation(state) for state in branch_states]

    return render(request, 'state/detail.html', {
        'statesList': formatted_states,
        'gitType': 'BRANCH',
        'gitName': branch_name,
        'gitCommit': gitCommitInfo(commitSHA),
    })


def resDictionary(width, height):
    return {
        'width': width,
        'height': height
    }


# return a dictionary {'state name': 'diff object'} of diffs using a head and base state.
def get_diff_images(head_state, base_state, width, height):

    # if no base state then
        # return nothing
    try:
        # these queries should only return 1 unique Image
        img_base_state = Image.objects.get(device_res_width=width,
                                           device_res_height=height,
                                           state=base_state)
    except Image.DoesNotExist:
        # the image for the base state is still processing or there is something wrong.
        return

    # if has base state and head state but no diff state
        # when the head state is not done rendering so no diff has been calculated
        # return a NEW diff object with a null diff image
    # if has base state but no head state so no diff
        # do the same as above
    try:
        img_head_state = Image.objects.get(device_res_width=width,
                                           device_res_height=height,
                                           state=head_state)
    except Image.DoesNotExist:
        return {'state_name': base_state.state_name, 'diff_obj': None}

    try:
        diff_obj = Diff.objects.get(target_img=img_base_state, source_img=img_head_state)
    except Diff.DoesNotExist:
        diff_obj = Diff(diff_img_file=None,
                        target_img=img_base_state,
                        source_img=img_head_state)
        diff_obj.save()
    return {'state_name': base_state.state_name, 'diff_obj': diff_representation(diff_obj)}


# retrieve all states with a matching PR number
def singlePR(request, pr_number, repo_name="", res_width="0", res_height="0"):
    diff_dict_list = []  # final output of a list of diffs for the particular PR
    res_dict_list = []  # final output of a list of dictionaries that represent resolutions

    PR_obj = PR.objects.get(git_repo=repo_name, git_pr_number=pr_number)

    # get all the states associated to the base branch
    for base_state in PR_obj.git_target_commit.state_set.all():
        # get the complimentary head state object for the base state object
        try:
            head_state = State.objects.get(state_name=base_state.state_name,
                                           git_commit=PR_obj.git_source_commit)
        except:
            print("Base State:{0} has no equivalent state in the Head of the PR".format(base_state.state_name))  # noqa: ignore=E501
            continue  # the next steps all rely on existence of a head and a base state

        # get a list of the different resolutions avaliable for the particular PR
        single_state_res_dict = []  # temporary list of resolutions to query images of a state
        for img in Image.objects.filter(state=base_state):
            new_res = {'width': img.device_res_width, 'height': img.device_res_height}
            if new_res not in res_dict_list:
                res_dict_list.append(new_res)
            if new_res not in single_state_res_dict:
                single_state_res_dict.append(new_res)

        # default when no resolution is specified, list all diffs convert width and height to int
        if (res_width == "0" and res_height == "0"):

            for unique_res in single_state_res_dict:
                # get the specific image for this particular state and resolution
                if get_diff_images(head_state,
                                   base_state,
                                   unique_res['width'],
                                   unique_res['height']):
                    diff_dict_list.append(get_diff_images(head_state,
                                                          base_state,
                                                          unique_res['width'],
                                                          unique_res['height']))
        else:
            if get_diff_images(head_state, base_state, int(res_width), int(res_height)):
                diff_dict_list.append(get_diff_images(head_state,
                                                      base_state,
                                                      int(res_width),
                                                      int(res_height)))
    return render(request, 'compare/diff.html', {
        'PR': pr_representation(PR_obj),
        'diff_dict_list': diff_dict_list,
        'res_dict_list': res_dict_list,
    })


# Helper function that returns all types of diffs from a PR
# types of diffs: changed_diffs, unchanged_diffs, deleted_diffs, new_diffs
# USED in view_pr controller and approve_pr api point
def get_all_diff_types_of_build(build_obj):
    changed_diffs = []
    approved_changed_diffs = []

    unchanged_diffs = []
    approved_unchanged_diffs = []
    for diff in build_obj.get_diffs():
        if diff.diff_percent > 0:
            changed_diffs.append(diff)
            if diff.is_approved:
                approved_changed_diffs.append(diff)
        else:
            unchanged_diffs.append(diff)
            if diff.is_approved:
                approved_unchanged_diffs.append(diff)

    # screenshots with state defined in source_commit (head) only
    new_diffs = build_obj.get_new_states_images()
    approved_new_diffs = []
    for image in new_diffs:
        if image.is_approved:
            approved_new_diffs.append(image)

    # screenshots forom target_commit (base) only
    deleted_diffs = build_obj.get_deleted_states_images()
    approved_deleted_diffs = []
    for image in deleted_diffs:
        if image.is_approved:
            approved_deleted_diffs.append(image)

    all_states = changed_diffs + unchanged_diffs + new_diffs + deleted_diffs
    all_approved_states = (approved_changed_diffs + approved_unchanged_diffs +
                           approved_new_diffs + approved_deleted_diffs)

    return {'changed':
            {'all': changed_diffs,
             'approved': approved_changed_diffs,
             'unapproved': set(changed_diffs).symmetric_difference(approved_changed_diffs)
             },
            'unchanged':
            {'all': unchanged_diffs,
             'approved': approved_unchanged_diffs,
             'unapproved': set(unchanged_diffs).symmetric_difference(approved_unchanged_diffs)
             },
            'new':
            {'all': new_diffs,
             'approved': approved_new_diffs,
             'unapproved': set(new_diffs).symmetric_difference(approved_new_diffs)
             },
            'deleted':
            {'all': deleted_diffs,
             'approved': approved_deleted_diffs,
             'unapproved': set(deleted_diffs).symmetric_difference(approved_deleted_diffs)
             },
            'total_states':
            {'all': all_states,
             'approved': all_approved_states,
             'unapproved': set(all_states).symmetric_difference(all_approved_states)
             }
            }


# The main page for viewing diffs.
def view_pr(request, repo_name, pr_number):
    # if request.user.is_authenticated:
    repo_name = urllib.unquote(repo_name)
    pr_obj = PR.objects.get(git_pr_number=pr_number)

    # display the last generated build diffs
    # Have a new header section for a new dectected build
    latest_build = pr_obj.get_latest_build()
    completed_build = pr_obj.get_last_executed_build()

    if completed_build and completed_build.status_code == 1:
        completed_build = None

    # if they are the same then only show completed_build
    if latest_build == completed_build:
        latest_build = None

    if completed_build:
        diff_types = get_all_diff_types_of_build(completed_build)
        return render(request, 'projects/pull/view_pr.html', {
                    'user': request.user.username,
                    'repo': repo_name,
                    'pr': pr_obj,
                    'new_build': latest_build,
                    'old_build': completed_build,
                    'history_list': pr_obj.history_set.all(),

                    'changed_diffs': diff_types['changed']['all'],
                    'approved_changed_diffs': diff_types['changed']['approved'],
                    'num_unapproved_changed_diffs': len(diff_types['changed']['unapproved']),

                    'unchanged_diffs': diff_types['unchanged']['all'],
                    'approved_unchanged_diffs': diff_types['unchanged']['approved'],
                    'num_unapproved_unchanged_diffs': len(diff_types['unchanged']['unapproved']),

                    'new_diffs': diff_types['new']['all'],
                    'approved_new_diffs': diff_types['new']['approved'],
                    'num_unapproved_new_diffs': diff_types['new']['unapproved'],

                    'deleted_diffs': diff_types['deleted']['all'],
                    'approved_deleted_diffs': diff_types['deleted']['approved'],
                    'num_unapproved_deleted_diffs': len(diff_types['deleted']['unapproved']),

                    'num_total_states': len(diff_types['total_states']['all']),
                    'num_total_approved_states': len(diff_types['total_states']['approved']) - len(diff_types['unchanged']['approved']),  # noqa: E501
                    'num_total_unapproved_states': len(diff_types['total_states']['unapproved']),
                })
    else:
        # new and old builds?
        return render(request, 'projects/pull/view_pr.html', {
                    'user': request.user.username,
                    'repo': repo_name,
                    'pr': pr_obj,
                    'new_build': latest_build,
                    'old_build': None,
                    'history_list': pr_obj.history_set.all(),
                })
    # else:
    #     return redirect('login')


def pr_history(request, repo_name, pr_number):
    pr_obj = PR.objects.get(git_pr_number=pr_number)
    return render(request, 'projects/pull/history.html', {
                'history_list': pr_obj.history_set.all(),
            })


def git_oauth_callback(request):
    if 'client_id' in request.session and 'client_secret' in request.session \
       and 'password' in request.session:
        url = 'https://github.com/login/oauth/access_token'
        data = {'client_id': request.session.get('client_id', ''),
                'client_secret': request.session.get('client_secret', ''),
                'code': request.GET['code']}

        headers = {'Accept': 'application/json'}

        git_oauth_reply = requests.post(url, data=data, headers=headers)
        if (git_oauth_reply.status_code == 200 or
           json.loads(git_oauth_reply.text)['access_token'] == 'bad_verification_code'):

            token = json.loads(git_oauth_reply.text)['access_token']
            user_info_url = 'https://api.github.com/user?access_token={0}'.format(token)
            git_user_info = requests.get(url=user_info_url, headers=headers)

            username = json.loads(git_user_info.text)['login']
            password = request.session['password']

            if username and User.objects.filter(username=username).count() < 1:
                user_obj = User.objects.create_user(username=username,
                                                    password=password,
                                                    email=request.session.get('email', ''),
                                                    first_name=request.session.get('first_name', ''),  # noqa: E501
                                                    last_name=request.session.get('last_name', ''))

                Profile.objects.create(user=user_obj,
                                       git_client_id=request.session.get('client_id', ''),
                                       git_client_secret=request.session.get('client_secret', ''),
                                       git_access_token=token)
                # delete all the sessions except for username since the rest will be not used
                try:
                    del request.session['client_id']
                    del request.session['client_secret']
                    del request.session['first_name']
                    del request.session['last_name']
                    del request.session['email']
                    del request.session['password']
                except KeyError:
                    pass
                request.session['username'] = username
                return redirect('projects')
            else:
                raise RuntimeError('This Github User Profile already exists')
    raise RuntimeError('ERROR there was a problem in the github authentication process')


def api_logout(request):
    logout_auth(request)
    return redirect('login')


@require_POST
def api_login(request):
    user = authenticate(username=request.POST['username'],
                        password=request.POST['password'])
    if user is not None:
        login_auth(request, user)
        return redirect('projects')
    else:
        return redirect('login', True)


@require_POST
def api_register(request):
    request.session['client_id'] = request.POST['client_id']
    request.session['client_secret'] = request.POST['client_secret']

    request.session['first_name'] = request.POST['first_name']
    request.session['last_name'] = request.POST['last_name']
    request.session['email'] = request.POST['email']

    request.session['password'] = request.POST['password']

    git_oauth_url = 'https://github.com/login/oauth/authorize?client_id={0}'\
                    .format(request.POST['client_id'])
    return redirect(git_oauth_url)


# run the new pr command when the webhook detects a PullRequestEvent
@csrf_exempt
@require_POST
def webhook(request):
    print 'git payload webhook coming in'
    try:
        payload = json.loads(request.body)
        act = payload['action']
        print('github action: ', act)
        if(act == "opened" or act == "reopened" or act == "closed" or act == "synchronized"):
            History.log_pr_action(payload['pr_number'], act, request.user)
            call_command('webhookHandler', payload['number'])
        return HttpResponse(status=200)
    except:
        # github webhook error
        return HttpResponse(status=500)


@csrf_exempt
@require_POST
def browserstack_callback(request, img_id):
    try:
        # get the payload from the callback
        bs_payload = json.loads(request.body)
    except Exception, e:
        print(str(e))
        return HttpResponse(status=500)

    # get the image object that has currently null image file and update it with bs url
    img_obj = Image.objects.get(id=img_id)
    img_obj.img_file = bs_payload['screenshots'][0]['image_url']
    print("BROWSER STACK image {0} completed rendering".format(img_obj.img_file.name))
    img_obj.save()

    dependent_diffs = img_obj.target_img_in_Diff.all() | img_obj.source_img_in_Diff.all()
    for diff in dependent_diffs:
        if (not diff.diff_image_rendered() and
                diff.target_img.image_rendered() and
                diff.source_img.image_rendered()):

            print 'Discovered new Diff to create ...'
            django_rq.get_queue('default').enqueue(gen_diff,
                                                   diff.target_img.img_file.name,
                                                   diff.source_img.img_file.name)
    return HttpResponse(status=200)


# view_pr "Generate" button starts this process does all the screenshots and diffing
@require_POST
def api_generate_diffs(request, repo_name, pr_number, base_commit, head_commit):
    call_command('auto-screenshot',
                 pr_number,
                 request.POST['base_host'],
                 request.POST['head_host'],
                 base_commit,
                 head_commit)

    return redirect('view_pr', repo_name, pr_number)


@require_POST
def approve_diff(request):
    if request.is_ajax():
        diff_or_img = request.POST.get('diff_or_img', None)

        if diff_or_img == 'diff':
            diff_obj_id = request.POST.get('diff_id', -1)
            try:
                obj = Diff.objects.get(id=diff_obj_id)
            except Diff.DoesNotExist:
                # For some reason the Diff was deleted or there was a Javascript checkbox error
                return HttpResponse(status=500)
        elif diff_or_img == 'img':
            img_obj_id = request.POST.get('img_id', -1)
            try:
                obj = Image.objects.get(id=img_obj_id)
            except Image.DoesNotExist:
                # For some reason the Diff was deleted or there was a Javascript checkbox error
                return HttpResponse(status=500)
        else:
            return HttpResponse(status=500)
        # toggle the diff.is_approved
        obj.is_approved = not obj.is_approved
        obj.save()

        # get an updated number of approved changed diffs
        pr_obj = PR.objects.get(git_pr_number=request.POST['pr_number'])

        diff_types = get_all_diff_types_of_build(pr_obj.get_last_executed_build())

        ajax_reply = {'num_changed': len(diff_types['changed']['all']),
                      'num_changed_approved': len(diff_types['changed']['approved']),

                      'num_unchanged': len(diff_types['unchanged']['all']),
                      'num_unchanged_approved': len(diff_types['unchanged']['approved']),

                      'num_new': len(diff_types['new']['all']),
                      'num_new_approved': len(diff_types['new']['approved']),

                      'num_deleted': len(diff_types['deleted']['all']),
                      'num_deleted_approved': len(diff_types['deleted']['approved']),

                      'num_approved_states': len(diff_types['total_states']['approved']),
                      'num_total_states': len(diff_types['total_states']['all'])
                      }
        return HttpResponse(json.dumps(ajax_reply), content_type='application/json')
    else:
        # the request was not in the expect form of an Ajax request
        return HttpResponse(status=400)
    return


@require_POST
def approve_img(request):
    if request.is_ajax():
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)


# api url from reset/Approve All button on view_diff page
@require_POST
def approve_or_reset_diffs(request):
    # get list of changed diffs set, set is_approved=true
    if request.is_ajax():
        pr_obj = PR.objects.get(git_pr_number=request.POST['pr_number'])
        latest_build = pr_obj.get_last_executed_build()

        if request.POST['reset_or_approve'] == 'approve':
            for diff in latest_build.get_diffs():
                # only approve diffs with changes
                diff.is_approved = True
                diff.save()
            for img in latest_build.get_new_states_images():
                img.is_approved = True
                img.save()

            for img in latest_build.get_deleted_states_images():
                img.is_approved = True
                img.save()

            return HttpResponse(status=200)
        elif request.POST['reset_or_approve'] == 'reset':
            # get list of changed diffs set, set is_approved=False
            for diff in latest_build.get_diffs():
                # only approve diffs with changes
                if diff.diff_percent > 0:
                    diff.is_approved = False
                else:
                    diff.is_approved = True
                diff.save()

            for img in latest_build.get_new_states_images():
                img.is_approved = False
                img.save()

            for img in latest_build.get_deleted_states_images():
                img.is_approved = False
                img.save()

            return HttpResponse(status=200)

    return HttpResponse(status=500)
