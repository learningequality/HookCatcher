import json
import requests
from django.conf import settings  # database dir
from django.core.management.base import BaseCommand, CommandError
from HookCatcher.models import State

STATES_FOLDER = 'states'  # folder within git repo that organizes the list of states

# header of the git GET request
GIT_HEADER = {
    'Authorization': 'token ' + settings.GIT_OAUTH,
}

# GIT_REPO_API example form "https://api.github.com/repos/MingDai/kolibri"
GIT_REPO_API = 'https://api.github.com/repos/{0}'.format(settings.GIT_REPO)


# Pass in the information about the PR
# access the state JSON files and saving data into models
def saveStates(gitBranchName, gitPRnumber, gitCommit, gitSourceType):
    # number of states that was saved for this commit
    numStatesAdded = 0

    # get the directory of the states folder with the JSON states
    statesDir = STATES_FOLDER + '?ref=' + gitCommit
    # example url https://api.github.com/repos/MingDai/kolibri/contents/states?ref=COMMIT_SHA
    gitContentURL = '{0}/contents/{1}'.format(GIT_REPO_API, statesDir)
    reqStatesList = requests.get(gitContentURL, headers=GIT_HEADER)

    if (reqStatesList.status_code == 200):
        statesList = json.loads(reqStatesList.text)
        # if stateList = 0, then exit as well because there are no states to add
        # if the states of this commit has already been added to database then don't add it again
        if(State.objects.filter(git_commit=gitCommit).count() < len(statesList)):
            # save the json content for each file of the STATES_FOLDER defined in user_settings
            for eachState in statesList:
                # get the raw json file for each state
                rawURL = eachState["download_url"]
                reqRawState = requests.get(rawURL, headers=GIT_HEADER)

                if (reqRawState.status_code == 200):
                    # save the json as a regular string rather than unicode using yaml
                    rawState = json.loads(reqRawState.text)

                    # is this a PR state or a branch state
                    if str(gitSourceType).upper() == 'PR':
                        gitSourceName = gitPRnumber
                    else:
                        gitSourceName = gitBranchName

                    s = State(state_name=rawState['name'],
                              state_desc=rawState['description'],
                              state_json=rawState['url'],
                              git_source_type=gitSourceType,
                              git_source_name=gitSourceName,
                              git_commit=gitCommit)
                    print(s)
                    # s.save()
                    numStatesAdded += 1

                else:
                    print('There was no json files within the folder {0}'.format(STATES_FOLDER))
        else:  # check for repeated commits make sure funciton is idempotent
            print('The states of the commit in branch "{0}" have already been added'.format(gitBranchName))  # noqa: E501
    else:
        print('The folder "{0}" is not found in commit {1}'.format(STATES_FOLDER, gitCommit))

    return numStatesAdded


class Command(BaseCommand):
    help = 'Fill the database with info about all the new states with a PR'

    def add_arguments(self, parser):
        # the Pull Request Number as argument
        parser.add_argument('prNumber', type=int)

    def handle(self, *args, **options):
        try:
            errorMessage = "Invalid input for PR number"

            prNumber = options['prNumber']
            # get the information about a certain PR through Github API
            gitPullURL = '{0}/pulls/{1}'.format(GIT_REPO_API, prNumber)
            reqSpecificPR = requests.get(gitPullURL, headers=GIT_HEADER)
            # make sure connection to Github API was successful
            if (reqSpecificPR.status_code == 200):
                self.stdout.write(self.style.SUCCESS('Accessing "{0}"'.format(gitPullURL)))
                specificPR = json.loads(reqSpecificPR.text)
                gitPRnumber = specificPR['number']

                # head of the Pull Request save branch name and commitSHA
                headBranchName = specificPR['head']['ref']
                headCommitSHA = specificPR['head']['sha']

                # Base of Pull Request save branch name and the commitSHA
                baseBranchName = specificPR['base']['ref']
                baseCommitSHA = specificPR['base']['sha']

                print("Adding States: ")
                numStatesAdded = 0  # counts the number of states that have been added to data
                # save the json state representations into the database
                numStatesAdded += saveStates(headBranchName, gitPRnumber, headCommitSHA, "PR")
                numStatesAdded += saveStates(baseBranchName, gitPRnumber, baseCommitSHA, "BRANCH")

                print("Successfully saved {0} new states".format(numStatesAdded))

            else:
                errorMessage = 'Could not retrieve PR {0} info from git repo'.format(prNumber)
        except State.DoesNotExist:
            raise CommandError(errorMessage)
