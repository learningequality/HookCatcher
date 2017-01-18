from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
# must import models and save to models
@csrf_exempt
def index(request):
	if request.method == 'POST':
		gitData = request.body
		gitJSON = json.loads(gitData)
		print '\nRaw Data: "%s"\n' % gitJSON['zen']
	return render(request, 'index.html',)

# Create your views here.
