# import json
# import requests
# import sh
import json
import os

import requests
from django.conf import settings  # database dir
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import State

GITHUB_PR_URL = 'https://github.com/MingDai/kolibri/pull/6/commits/'


IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')  # assume an img folder in database


@csrf_exempt
def index(request):
    return render(request, 'index.html')


# store all info about a state into one object
def stateRepresentation(stateObj):
    return {
        'name': stateObj.state_name,
        'desc': stateObj.state_desc,
        'gitType': stateObj.git_source_type,
        'gitName': stateObj.git_source_name,
        'gitCommitSHA': stateObj.git_commit[:7],
        'imgsOfState': stateObj.image_set.all()
    }


# only take the information needed from JSON response
def gitRepresentation(gitJSON):
    return {
        'url': gitJSON['html_url'],
        'author': gitJSON['commit']['author']['name'],
        'date': gitJSON['commit']['author']['date'],
        'filesChanged': len(gitJSON['files'])
    }


# get request to github API
def gitCommit(gitSHA):
    headers = {
        'Authorization': 'token ' + settings.GIT_OAUTH,
    }

    gitRepoURL = os.path.join(settings.GIT_REPO_API, 'commits')
    gitCommitURL = os.path.join(gitRepoURL, gitSHA)
    getCommit = requests.get(gitCommitURL, headers=headers)

    if(getCommit.ok):
        gitJSON = json.loads(getCommit.text)
        return gitRepresentation(gitJSON)


# retrieve all states with a matching branch name
def singleBranch(request, branchName, commitSHA):
    branchStates = State.objects.filter(git_source_type='BRANCH')
    allStates = branchStates.filter(git_source_name=branchName)
    formattedStates = [stateRepresentation(state) for state in allStates]

    gitInfo = gitCommit(commitSHA)
    return render(request, 'state/detail.html', {
        'states_list': formattedStates,
        'gitType': 'BRANCH',
        'gitName': branchName,
        'gitCommit': gitInfo,
    })


# retrieve all states with a matching PR number
def singlePR(request, prNumber, commitSHA):
    prStates = State.objects.filter(git_source_type='PR')
    allStates = prStates.filter(git_source_name=prNumber)
    formattedStates = [stateRepresentation(state) for state in allStates]

    gitInfo = gitCommit(commitSHA)
    return render(request, 'state/detail.html', {
        'states_list': formattedStates,
        'gitType': 'PR',
        'gitName': prNumber,
        'gitCommit': gitInfo,
    })


# retrieve the data of a specific image from data directory
def getImage(request, imageID):
    print('IMAGEEE' + imageID)
    imageDir = os.path.join(IMG_DATABASE_DIR, imageID)
    imageData = open(imageDir, "rb").read()
    return HttpResponse(imageData, content_type="image/png")


# retrieve all states from State model
def allStates(request):
    allStates = State.objects.all()
    formattedStates = [stateRepresentation(state) for state in allStates]
    return render(request, 'state/index.html', {
        'states_list': formattedStates,
    })


'''
def BSresponse(request):
    if request.method == 'POST':
        JSONbsReply = json.loads(request.body)
        print 'Callback Reply: "%s"\n' % JSONbsReply
    return render(request, 'BSresponse/index.html')
'''
