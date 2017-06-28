import json
import os

import requests
from django.conf import settings  # database dir
from django.core.management import call_command  # call newPR update command
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import PR, Commit, Diff, Image, State

IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')  # assume an img folder in database


# store all info about a state into one object
def stateRepresentation(stateObj):
    return {
        'name': stateObj.stateName,
        'desc': stateObj.stateDesc,
        'url': stateObj.stateUrl,
        'gitRepo': stateObj.gitRepo,
        'gitBranch': stateObj.gitBranch,
        'gitCommitSHA': stateObj.gitCommit.gitHash,
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
    uniqueRepos = Commit.objects.order_by().values('gitRepo').distinct()
    return render(request, 'index.html', {
        'repoList': uniqueRepos,
    })


# retrieve all states with a matching branch name
def singleBranch(request, branchName, commitSHA):
    branchStates = State.objects.filter(gitBranch=branchName)
    formattedStates = [stateRepresentation(state) for state in branchStates]

    gitInfo = gitCommitInfo(commitSHA)
    return render(request, 'state/detail.html', {
        'statesList': formattedStates,
        'gitType': 'BRANCH',
        'gitName': branchName,
        'gitCommit': gitInfo,
    })


def listPR(request, gitRepo=""):
    prList = PR.objects.filter(gitRepo=gitRepo).order_by('-gitPRNumber')
    return render(request, 'compare/index.html', {
        'prList': prList,
    })


def resDictionary(width, height):
    return {
        'width': width,
        'height': height
    }


def diffDictionary(stateName, diffObj):
    return {
        'stateName': stateName,
        'diffObj': diffObj
    }


# retrieve all states with a matching PR number
def singlePR(request, prNumber, repoName="MingDai/kolibri", resWidth="0", resHeight="0"):
    diffDictList = []  # final output of a list of diffs for the particular PR
    listResDict = []  # final output of a list of dictionaries that represent resolutions

    PRobj = PR.objects.get(gitRepo=repoName, gitPRNumber=prNumber)
    # bases the states on the base branch where the PR is located
    # in case list of states for head and base is unique
    baseStates = PRobj.gitTargetCommit.state_set.all()

    for baseState in baseStates:
        # get the headState stateName should match that of the baseState
        try:
            headState = State.objects.get(stateName=baseState.stateName,
                                          gitCommit=PRobj.gitSourceCommit)
        except:
            print("Base State:{0} has no equivalent state in the Head of the PR".format(baseState.stateName))  # noqa: ignore=E501

        # get a list of different resolution optoins avaliable for the particular PR
        tempListResDict = []  # temporary list of resolutions to query images for particualr state
        for img in Image.objects.filter(state=baseState):
            newRes = resDictionary(img.width, img.height)
            if newRes not in listResDict:
                listResDict.append(newRes)
            if newRes not in tempListResDict:
                tempListResDict.append(newRes)

        # check to see if a resolution was given for a single state. convert width and height to int
        if (resWidth == "0" and resHeight == "0"):

            for uniqueRes in tempListResDict:
                # get the specific image for this particular state and resolution
                try:
                    # these queries should only return 1 unique Image
                    imgBaseState = Image.objects.get(width=uniqueRes['width'],
                                                     height=uniqueRes['height'],
                                                     state=baseState)

                    imgHeadState = Image.objects.get(width=uniqueRes['width'],
                                                     height=uniqueRes['height'],
                                                     state=headState)

                    diffObj = Diff.objects.get(targetImg=imgBaseState, sourceImg=imgHeadState)

                    diffDict = diffDictionary(baseState.stateName, diffObj)
                    diffDictList.append(diffDict)
                except:
                    # either there is no Image for the head or base
                    # more than one Image for the head or base
                    # more than 1 Diff or no Diff was found
                    print("No diff for state {0} resolution {1}x{2}".format(baseState,
                                                                            uniqueRes['width'],
                                                                            uniqueRes['height']))
        else:
            # convert given resolutions from strings to int
            resWidth = int(resWidth)
            resHeight = int(resHeight)

            # get the specific image for this particular state and resolution
            try:
                # these queries should only return 1 unique Image
                imgBaseState = Image.objects.get(width=resWidth, height=resHeight, state=baseState)

                imgHeadState = Image.objects.get(width=resWidth, height=resHeight, state=headState)

                diffObj = Diff.objects.get(targetImg=imgBaseState, sourceImg=imgHeadState)

                diffDict = diffDictionary(baseState.stateName, diffObj)
                diffDictList.append(diffDict)
            except:
                # either there is no Image for the head or base
                # more than one Image for the head or base
                # more than 1 Diff or no Diff was found
                print("There was no diff for state {0} in resolution {1}x{2}".format(baseState,
                                                                                     resWidth,
                                                                                     resHeight))

    return render(request, 'compare/diff.html', {
        'PR': PRobj,
        'diffDictList': diffDictList,
        'resDictList': listResDict,
    })


# retrieve all states with a matching PR number
def singleCommit(request, gitCommitSHA):
    commitObj = Commit.objects.filter(gitHash=gitCommitSHA)
    states = State.objects.get(gitCommit=commitObj)

    formattedStates = [stateRepresentation(state) for state in states]

    gitInfo = gitCommitInfo(commitObj.gitHash)
    return render(request, 'state/detail.html', {
        'statesList': formattedStates,
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
    print("TRYING TO GET THIS IMAGE: {0}".format(imageID))
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
            call_command('auto-screenshot', payload['number'])
        return HttpResponse(status=200)
    except:
        return HttpResponse(status=500)
