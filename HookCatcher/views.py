# import json
# import requests
# import sh
import os

from django.conf import settings  # database dir
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import State

URL_BASE = 'https://github.com/MingDai/kolibri/pull/6/commits/'


IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')  # assume an img folder in database
print(IMG_DATABASE_DIR)


# must import models and save to models
@csrf_exempt
def index(request):

    '''
    GITHUB WEBHOOK HANDLER

    if request.method == 'POST':
        gitData = request.body
        gitJSON = json.loads(gitData)
        print '\nRaw Data: "%s"\n' % gitJSON['zen']

'''
    '''
    BROWSERSTACK API HANDLER

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    kolibriURL =
    "http://39782c5f.ngrok.io/learn/#/explore/5b1e904335ab4dfda82e3e37735262c5"

    appAPIURL = "http://0649192a.ngrok.io/BSresponse/"

    data = '{
    "url":
    "http://39782c5f.ngrok.io/learn/#/explore/5b1e904335ab4dfda82e3e37735262c5",
    "callback_url": "http://0649192a.ngrok.io/BSresponse/",
    "win_res": "1024x768",
    "mac_res": "1920x1080",
    "quality": "compressed",
    "wait_time": 60,
    "orientation": "portrait",
    "browsers":[{"os": "Windows",
    "os_version": "7",
    "browser_version":
    "9.0", "browser": "ie"}]
    }'

    postRequest = requests.post('https://www.browserstack.com/screenshots',
                                headers=headers,
                                data=data,
                                auth=('mingdai1', 'dfTNku6CERcRaExPs6KF'))
    print 'Response Text: "%s"\n' % postRequest.text
    '''
    return render(request, 'index.html')


# store all info about a state into one object
def stateRepresentation(stateObj):
    return {
        'name': stateObj.state_name,
        'desc': stateObj.state_desc,
        'gitType': stateObj.git_source_type,
        'gitName': stateObj.git_source_name,
        'gitCommitURL': URL_BASE + stateObj.git_commit,
        'imgsOfState': stateObj.image_set.all()
    }


# retrieve all states with a matching branch name
def singleBranch(request, branchName):
    branchStates = State.objects.filter(git_source_type='BRANCH')
    allStates = branchStates.filter(git_source_name=branchName)
    formattedStates = [stateRepresentation(state) for state in allStates]
    return render(request, 'state/detail.html', {
        'states_list': formattedStates,
        'gitType': 'BRANCH',
        'gitName': branchName
    })


# retrieve all states with a matching PR number
def singlePR(request, prNumber):
    prStates = State.objects.filter(git_source_type='PR')
    allStates = prStates.filter(git_source_name=prNumber)
    formattedStates = [stateRepresentation(state) for state in allStates]
    return render(request, 'state/detail.html', {
        'states_list': formattedStates,
        'gitType': 'PR',
        'gitName': prNumber,
    })


# retrieve the data of a specific image from data directory
def getImage(request, imageID):
    print('IMAGEEE' + imageID)
    image_dir = os.path.join(IMG_DATABASE_DIR, imageID)
    image_data = open(image_dir, "rb").read()
    return HttpResponse(image_data, content_type="image/png")


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
