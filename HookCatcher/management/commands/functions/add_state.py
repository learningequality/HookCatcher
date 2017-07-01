import json
import os
import requests

from django.conf import settings  # database dir
from django.core.management.base import CommandError
from HookCatcher.models import Commit, State

GIT_HEADER = {
    'Authorization': 'token ' + settings.GIT_OAUTH,
}


# get a Commit Object using a Commit SHA from database
def saveCommit(gitRepoName, gitBranchName, gitCommitSHA):
    # check if this commit is already in database
    if(Commit.objects.filter(gitRepo=gitRepoName,
                             gitBranch=gitBranchName,
                             gitHash=gitCommitSHA).count() <= 0):
        commitObj = Commit(gitRepo=gitRepoName,
                           gitBranch=gitBranchName,
                           gitHash=gitCommitSHA)
        commitObj.save()
        print('Adding states of new commit "{0}"'.format(gitCommitSHA[:7]))
        return commitObj
    else:
        return Commit.objects.get(gitRepo=gitRepoName,
                                  gitBranch=gitBranchName,
                                  gitHash=gitCommitSHA)


# Read a single json file that represents a state and save into models
# save the commit object into the database
def add_state(statePath, gitRepoName, gitBranchName, gitCommitSHA):
    # check if the path to the json is valid
    if(os.path.exists(statePath) is True):
        with open(statePath, 'r') as s:
            rawState = json.loads(s.read())

    # if the user inputted a URL to the json instead of a local file
    else:
        req = requests.get(statePath, headers=GIT_HEADER)
        if(req.status_code == 200):
            rawState = json.loads(req.text)
        else:
            raise CommandError('The inputted JSON file location is invalid')

    # SUCEEDED in finding the file

    # get the commit object from the commit hash
    commitObj = saveCommit(gitRepoName, gitBranchName, gitCommitSHA)

    findState = State.objects.filter(stateName=rawState['name'],
                                     stateDesc=rawState['description'],
                                     stateUrl=rawState['url'],
                                     gitCommit=commitObj)

    if (findState.count() < 1):
        s = State(stateName=rawState['name'],
                  stateDesc=rawState['description'],
                  stateUrl=rawState['url'],
                  gitCommit=commitObj)
        s.save()
        print('Finished adding state: %s' % s)
        return s
    else:
        return
