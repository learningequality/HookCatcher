from django.shortcuts import render
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt
from .models import State, Image, Diff

import json, requests
import sh

URL_BASE = "https://github.com/MingDai/kolibri/pull/6/commits/"

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

	kolibriURL = "http://39782c5f.ngrok.io/learn/#/explore/5b1e904335ab4dfda82e3e37735262c5"
	appAPIURL = "http://0649192a.ngrok.io/BSresponse/"

	data = '{"url": "http://39782c5f.ngrok.io/learn/#/explore/5b1e904335ab4dfda82e3e37735262c5", "callback_url": "http://0649192a.ngrok.io/BSresponse/", "win_res": "1024x768", "mac_res": "1920x1080", "quality": "compressed", "wait_time": 60, "orientation": "portrait", "browsers":[{"os": "Windows", "os_version": "7", "browser_version": "9.0", "browser": "ie"}]}'

	postRequest = requests.post('https://www.browserstack.com/screenshots', headers=headers, data=data, auth=('mingdai1', 'dfTNku6CERcRaExPs6KF'))
	print 'Response Text: "%s"\n' % postRequest.text
	'''
	return render(request, 'index.html')

def stateRepresentation(stateObj):
	#get all the URLs of the images that are of this state
	return {
		'name': stateObj.state_name,
		'desc': stateObj.state_desc,
		'gitType': stateObj.git_source_type,
		'gitName': stateObj.git_source_name,
		'gitCommitURL': URL_BASE + stateObj.git_commit,
		'imgsOfState': stateObj.image_set.all()
		}

def singleState(request, gitSource, gitSourceID):
	gitSource = gitSource.upper()
	if (gitSource.upper() != 'BRANCH' and gitSource.upper() != 'PR'):
		raise Http404("Choose a Github Branch or PR to view")

	allStates = State.objects.filter(git_source_type=gitSource).filter(git_source_name=gitSourceID)
	statesFormatted = [stateRepresentation(state) for state in allStates]

	return render(request, 'state/detail.html',{'states_list': statesFormatted, 'gitType': gitSource, 'gitName': gitSourceID})


def allStates(request):
	allStates = State.objects.all()
	statesFormatted = [stateRepresentation(state) for state in allStates]
	return render(request, 'state/index.html',{'states_list': statesFormatted, 'states_length': len(statesFormatted)})


def allDiffs(request):
		
	return 

def BSresponse(request):
	'''
	if request.method == 'POST':
		JSONbsReply = json.loads(request.body)
		print 'Callback Reply: "%s"\n' % JSONbsReply
	'''
	return render(request, 'BSresponse/index.html')
# Create your views here.
