from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json, requests
# must import models and save to models
@csrf_exempt
def index(request):
	

	'''if request.method == 'POST':
		gitData = request.body
		gitJSON = json.loads(gitData)
		print '\nRaw Data: "%s"\n' % gitJSON['zen']
	
	'''
	headers = {
	    'Content-Type': 'application/json',
	    'Accept': 'application/json',
	}

	data = '{"url": "https://learningequality.org/about/team/", "callback_url": "http://82019d72.ngrok.io", "win_res": "1024x768", "mac_res": "1920x1080", "quality": "compressed", "wait_time": 60, "orientation": "portrait", "browsers":[{"os": "Windows", "os_version": "7", "browser_version": "9.0", "browser": "ie"}]}'

	postRequest = requests.post('https://www.browserstack.com/screenshots', headers=headers, data=data, auth=('mingdai1', 'dfTNku6CERcRaExPs6KF'))
	print 'Request Text: "%s"\n' % postRequest.text

	bsReply = request.body
	JSONbsReply = json.loads(bsReply)
	print '\nRequest Body: "%s"\n' % JSONbsReply

	return render(request, 'index.html',)

# Create your views here.
