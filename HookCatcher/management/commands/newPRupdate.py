import json
import os

import requests
import yaml  # for parsing unicode json to strings
from django.conf import settings  # database dir
from django.core.management.base import BaseCommand, CommandError
from HookCatcher.models import State

STATES_FOLDER = 'states'  # folder within git repo that organizes the list of states
# header of the git GET request
GIT_HEADER = {
    'Authorization': 'token ' + settings.GIT_OAUTH,
}


# function for accessing state JSON files and saving data into models
def saveStates(gitBranch, gitPRnumber, gitCommit, gitSourceType):
    # get the directory location of the states folder with the JSON states
    gitContentURLtemp = os.path.join(settings.GIT_REPO_API, 'contents')
    statesDir = STATES_FOLDER + '?ref=' + gitBranch
    # example url https://api.github.com/repos/MingDai/kolibri/contents/states?ref=test-pr
    gitContentURL = os.path.join(gitContentURLtemp, statesDir)
    reqStatesDir = requests.get(gitContentURL, headers=GIT_HEADER)
    jsonStatesDir = json.loads(reqStatesDir.text)

    # save the json content for each file of the STATES_FOLDER
    for eachState in jsonStatesDir:
        # get the raw json file for each state
        rawURL = eachState["download_url"]
        reqRawState = requests.get(rawURL, headers=GIT_HEADER)
        # save the json as a regular string rather than a unicode with yaml
        jsonRawState = yaml.safe_load(reqRawState.text)

        if str(gitSourceType).upper() == 'PR':
            gitSourceName = gitPRnumber
        else:
            gitSourceName = gitBranch

        s = State(state_name=jsonRawState['name'],
                  state_desc=jsonRawState['description'],
                  state_json=jsonRawState,
                  git_source_type=gitSourceType,
                  git_source_name=gitSourceName,
                  git_commit=gitCommit)
        s.save()


class Command(BaseCommand):
    help = 'Fill the database with info about all the new states with a PR'

    def add_arguments(self, parser):
        # the Pull Request Number as argument
        parser.add_argument('prNumber', nargs='+', type=int)

    def handle(self, *args, **options):
        for prNumber in options['prNumber']:
            try:
                errorMessage = "Invalid input for PR number"

                # get the name of the head branch of the certain PR
                gitPullURLtemp = os.path.join(settings.GIT_REPO_API, 'pulls')
                gitPullURL = os.path.join(gitPullURLtemp, str(prNumber))
                reqSpecificPR = requests.get(gitPullURL, headers=GIT_HEADER)
                if (reqSpecificPR.ok):
                    self.stdout.write(self.style.SUCCESS('Accessing "{0}"'.format(gitPullURL)))
                    jsonSpecificPR = json.loads(reqSpecificPR.text)

                    gitPRnumber = jsonSpecificPR['number']
                    # head of the Pull Request
                    headBranchName = jsonSpecificPR['head']['ref']
                    headCommitSHA = jsonSpecificPR['head']['sha']

                    # Base of the Pull Request
                    baseBranchName = jsonSpecificPR['base']['ref']
                    baseCommitSHA = jsonSpecificPR['base']['sha']

                    # save the json state representations into the database
                    saveStates(headBranchName, gitPRnumber, headCommitSHA, "PR")
                    saveStates(baseBranchName, gitPRnumber, baseCommitSHA, "BRANCH")

                else:
                    errorMessage = 'Could not retrieve PR {0} info from git repo'.format(prNumber)
            except State.DoesNotExist:
                raise CommandError(errorMessage)
