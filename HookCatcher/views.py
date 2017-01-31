from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import State, Image, Diff
import json, requests
import sh

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
	

	return render(request, 'index.html',)

def BSresponse(request):
	'''
	if request.method == 'POST':
		JSONbsReply = json.loads(request.body)
		print 'Callback Reply: "%s"\n' % JSONbsReply
	'''
	return render(request, 'BSresponse/index.html')
# Create your views here.
