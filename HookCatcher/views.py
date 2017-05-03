import json
import os
import requests

from django.conf import settings  # database dir
from django.core.management import call_command  # call newPR update command
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import State

IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')  # assume an img folder in database


@csrf_exempt
def index(request):
    return render(request, 'index.html')


# store all info about a state into one object
def stateRepresentation(stateObj):
    return {
        'name': stateObj.stateName,
        'desc': stateObj.stateDesc,
        'url': stateObj.stateUrl,
        'gitRepo': stateObj.gitRepo,
        'gitBranch': stateObj.gitBranch,
        'gitCommitSHA': stateObj.gitCommit.gitHash[:7],
        'imgsOfState': stateObj.image_set.all()
    }


# only take the information needed from JSON response
def gitCommitRepresentation(gitInfo):
    return {
        'url': gitInfo['html_url'],
        'author': gitInfo['commit']['author']['name'],
        'date': gitInfo['commit']['author']['date'],
        'filesChanged': len(gitInfo['files'])
    }


# get request to github API
def gitCommit(gitSHA):
    headers = {
        'Authorization': 'token ' + settings.GIT_OAUTH,
    }
    # ex. commit url = https://github.com/MingDai/kolibri/pull/6/commits/
    gitRepoURL = os.path.join(settings.GIT_REPO_API, 'commits')
    gitCommitURL = os.path.join(gitRepoURL, gitSHA)
    getCommit = requests.get(gitCommitURL, headers=headers)

    if(getCommit.status_code == 200):
        gitCommitObj = json.loads(getCommit.text)
        return gitCommitRepresentation(gitCommitObj)


# retrieve all states with a matching branch name
def singleBranch(request, branchName, commitSHA):
    branchStates = State.objects.filter(gitBranch=branchName)
    formattedStates = [stateRepresentation(state) for state in branchStates]

    gitInfo = gitCommit(commitSHA)
    return render(request, 'state/detail.html', {
        'statesList': formattedStates,
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
        'statesList': formattedStates,
        'gitType': 'PR',
        'gitName': prNumber,
        'gitCommit': gitInfo,
    })


# retrieve all states from State model
def allStates(request):
    allStates = State.objects.all()
    formattedStates = [stateRepresentation(state) for state in allStates]
    return render(request, 'state/index.html', {
        'statesList': formattedStates,
    })


# retrieve the data of a specific image from data directory
def getImage(request, imageID):
    imageDir = os.path.join(IMG_DATABASE_DIR, imageID)
    imageData = open(imageDir, "rb").read()
    return HttpResponse(imageData, content_type="image/png")


# run the new pr command when the webhook detects a PullRequestEvent
@csrf_exempt
@require_POST
def webhook(request):
    try:
        payload = json.loads(request.body)
        act = payload['action']
        print('github action:', act)
        if(act == "opened" or act == "reopened" or act == "closed" or act == "synchronized"):
            call_command('w', payload['number'])
        return HttpResponse(status=200)
    except:
        return HttpResponse(status=500)
