import json
import os
import requests

from django.conf import settings  # database dir
from django.core.management.base import BaseCommand, CommandError
from HookCatcher.models import Commit, State

GIT_HEADER = {
    'Authorization': 'token ' + settings.GIT_OAUTH,
}


# Read a single json file that represents a state and save into models
# save the commit object into the database
def addState(rawState, gitRepoName, gitBranchName, gitCommitObj):
    # get the raw json file for each state
    s = State(stateName=rawState['name'],
              stateDesc=rawState['description'],
              stateUrl=rawState['url'],
              gitRepo=gitRepoName,
              gitBranch=gitBranchName,
              gitCommit=gitCommitObj)
    s.save()
    print(s)


class Command(BaseCommand):
    help = 'Add a state into the states table'

    def add_arguments(self, parser):
        # need to open the JSON file from the path
        parser.add_argument('pathToJSONfile')
        parser.add_argument('gitRepo')
        parser.add_argument('gitBranch')
        parser.add_argument('gitCommitHash')

    def handle(self, *args, **options):
        jsonPath = options['pathToJSONfile']

        # check if the path to the json is valid
        if(os.path.exists(options['pathToJSONfile']) is True):
            contents = json.loads(open(jsonPath, 'r').read())

        # if the user inputted a URL to the json instead of a local file
        else:
            req = requests.get(jsonPath, headers=GIT_HEADER)
            if(req.status_code == 200):
                contents = json.loads(req.text)
            else:
                raise CommandError('The inputted JSON file location is invalid')

        # SUCEEDED in finding the file

        # get the commit object from the commit hash
        commitObj = Commit(gitHash=options['gitCommitHash'])
        commitObj.save()
        addState(contents,
                 options['gitRepo'],
                 options['gitBranch'],
                 commitObj)
