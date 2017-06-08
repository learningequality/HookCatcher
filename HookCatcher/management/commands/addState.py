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
    findState = State.objects.filter(stateName=rawState['name'],
                                     stateDesc=rawState['description'],
                                     stateUrl=rawState['url'],
                                     gitRepo=gitRepoName,
                                     gitBranch=gitBranchName,
                                     gitCommit=gitCommitObj)

    if (findState.count() < 1):
        s = State(stateName=rawState['name'],
                  stateDesc=rawState['description'],
                  stateUrl=rawState['url'],
                  gitRepo=gitRepoName,
                  gitBranch=gitBranchName,
                  gitCommit=gitCommitObj)
        s.save()
        return s
    else:
        return


class Command(BaseCommand):
    help = 'Add a state into the states table'

    def add_arguments(self, parser):
        # need to open the JSON file from the path
        parser.add_argument('pathToJSONfile')
        parser.add_argument('gitRepo')
        parser.add_argument('gitBranch')
        parser.add_argument('gitCommitHash')

    def handle(self, *args, **options):
        statePath = options['pathToJSONfile']

        # check if the path to the json is valid
        if(os.path.exists(statePath) is True):
            contents = json.loads(open(statePath, 'r').read())

        # if the user inputted a URL to the json instead of a local file
        else:
            req = requests.get(statePath, headers=GIT_HEADER)
            if(req.status_code == 200):
                contents = json.loads(req.text)
            else:
                raise CommandError('The inputted JSON file location is invalid')

        # SUCEEDED in finding the file

        # get the commit object from the commit hash
        if (Commit.objects.filter(gitHash=options['gitCommitHash']).count() > 0):
            commitObj = Commit.objects.get(gitHash=options['gitCommitHash'])
        else:
            commitObj = Commit(gitHash=options['gitCommitHash'])
            commitObj.save()

        # get the state object from user input
        s = addState(contents,
                     options['gitRepo'],
                     options['gitBranch'],
                     commitObj)
        # if a new state was added
        if(s):
            self.stdout.write(self.style.SUCCESS('Finished adding state: %s' % s))
        else:
            raise CommandError('The specified state already exists')
