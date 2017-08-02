import json
import os

import requests
from django.conf import settings  # database dir
from django.core.management import call_command  # call newPR update command
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from HookCatcher.management.commands.functions.gen_diff import gen_diff

from .models import PR, Commit, Diff, Image, State

IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')  # assume an img folder in database

def is_url(img_file_name):
    validator = URLValidator()
    try:
        validator(img_file_name)
        return True
    except ValidationError:
        return False


# representation for all the models so you don't have to change every value for models in every template
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
        'url': state_obj.state_url,
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
    return {
        'name': image_obj.img_file.name if is_url(image_obj.img_file.name) else os.path.join(settings.MEDIA_URL, image_obj.img_file.name),
        'browser_type': image_obj.browser_type,
        'operating_system': image_obj.operating_system,
        'width': image_obj.device_res_width,
        'height': image_obj.device_res_height,
        'state': state_representation(image_obj.state)
    }


def diff_representation(diff_obj):
    file_name = None
    if diff_obj.diff_img_file.name:
        if is_url(diff_obj.diff_img_file.name):
            file_name = diff_obj.diff_img_file.name 
        else:
            file_name = os.path.join(settings.MEDIA_URL, diff_obj.diff_img_file.name)
            
    return { 
        'name': file_name,
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


def index(request):
    unique_repos = Commit.objects.order_by().values('git_repo').distinct()
    return render(request, 'index.html', {
        'repoList': unique_repos,
    })


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


def listPR(request, git_repo=""):
    pr_list = PR.objects.filter(git_repo=git_repo).order_by('-git_pr_number')
    return render(request, 'compare/index.html', {
        'prList': pr_list,
        'gitRepo': git_repo
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
def singlePR(request, pr_number, repo_name="MingDai/kolibri", res_width="0", res_height="0"):
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
        single_state_res_dict = []  # temporary list of resolutions to query images for particualr state
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
                if get_diff_images(head_state, base_state, unique_res['width'], unique_res['height']):
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


# retrieve the data of a specific image from data directory
def getImage(request, image_name, is_diff): 
    if is_diff == 'True':
        print("TRYING TO GET THIS IMAGE: {0}. diff count: {1}".format(image_name, Diff.objects.filter(diff_img_file=image_name).count()))
        # image_name needs to be full path including media/img
        diffQuery = Diff.objects.get(diff_img_file=image_name)
        imageData = diffQuery.img_file.open()
    else:
        print("TRYING TO GET THIS IMAGE: {0}. img count: {1}".format(image_name, Image.objects.filter(img_file=image_name).count()))
        # image_name needs to be full path including media/img
        imageQuery = Image.objects.get(img_file=image_name)
        imageData = imageQuery.img_file.open()
    return HttpResponse(imageData, mimetype="image/png")


# run the new pr command when the webhook detects a PullRequestEvent
@csrf_exempt
@require_POST
def webhook(request):
    try:
        payload = json.loads(request.body)
        act = payload['action']
        print('github action: ', act)
        if(act == "opened" or act == "reopened" or act == "closed" or act == "synchronized"):
            call_command('auto-screenshot', payload)
        return HttpResponse(status=200)
    except:
        # github webhook error
        return HttpResponse(status=500)

# Helper method to check if the image is currently loading or not. Return True if loaded
def img_loaded(img_file):
    return not img_file == None and not img_file.name == ''

@csrf_exempt
@require_POST
def browserstack_callback(request, img_id):
    print img_id
    try:
        # get the payload from the callback
        bs_payload = json.loads(request.body)
        print("BROWSER STACK image completed rendering")
    except Exception, e:
        print(str(e))
        return HttpResponse(status=500)

    # get the image object that has currently null image file and supply it with the url of the image
    img_obj = Image.objects.get(id=img_id)
    img_obj.img_file = bs_payload['screenshots'][0]['image_url']
    img_obj.save()

    dependent_diffs = img_obj.target_img_in_Diff.all() | img_obj.source_img_in_Diff.all()
    for diff in dependent_diffs:
        if not img_loaded(diff.diff_img_file) and img_loaded(diff.target_img.img_file) and img_loaded(diff.source_img.img_file):
            print 'Discovered new Diff to create'
            gen_diff('imagemagick',
                     diff.target_img.img_file.name,
                     diff.source_img.img_file.name)
    return HttpResponse(status=200)

