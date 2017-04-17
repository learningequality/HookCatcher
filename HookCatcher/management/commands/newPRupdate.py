import json

import requests
from django.conf import settings  # database dir
from django.core.management.base import BaseCommand, CommandError
from HookCatcher.models import PR, Commit, State

STATES_FOLDER = settings.STATES_FOLDER  # folder within git repo that organizes the list of states

# header of the git GET request
GIT_HEADER = {
    'Authorization': 'token ' + settings.GIT_OAUTH,
}

# GIT_REPO_API example form "https://api.github.com/repos/MingDai/kolibri"
GIT_REPO_API = 'https://api.github.com/repos/{0}'.format(settings.GIT_REPO)


# Read a single json file that represents a state and save into models
# save the commit object into the database
def parseStateJSON(stateRepresentation, gitRepoName, gitBranchName, gitCommitObj):
    # get the raw json file for each state
    rawURL = stateRepresentation["download_url"]
    reqRawState = requests.get(rawURL, headers=GIT_HEADER)

    if (reqRawState.status_code == 200):
        # save the json as a regular string rather than unicode using yaml
        rawState = json.loads(reqRawState.text)

        s = State(stateName=rawState['name'],
                  stateDesc=rawState['description'],
                  stateUrl=rawState['url'],
                  gitRepo=gitRepoName,
                  gitBranch=gitBranchName,
                  gitCommit=gitCommitObj)
        s.save()
        return 1

    else:
        print('There was no json files within the folder {0}'.format(STATES_FOLDER))

    return 0


# Pass in the information about the PR
# Access the state JSON files and saving data into models
def saveStates(gitRepoName, gitBranchName, gitCommitObj):
    # number of states that was saved for this commit
    numStatesAdded = 0

    # get the directory of the states folder with the JSON states
    statesDir = '{0}?ref={1}'.format(STATES_FOLDER, gitCommitObj.gitHash)
    # example url https://api.github.com/repos/MingDai/kolibri/contents/states?ref=9852bee670c
    gitContentURL = '{0}/contents/{1}'.format(GIT_REPO_API, statesDir)
    reqStatesList = requests.get(gitContentURL, headers=GIT_HEADER)

    if (reqStatesList.status_code == 200):
        statesList = json.loads(reqStatesList.text)
        # if stateList = 0, then exit as well because there are no states to add
        # if the states of this commit has already been added to database then don't add it again

        # filter gitHash first
        if(State.objects.filter(gitCommit=gitCommitObj).count() < len(statesList)):
            # save the json content for each file of the STATES_FOLDER defined in user_settings
            for eachState in statesList:
                numStatesAdded += parseStateJSON(eachState,
                                                 gitRepoName,
                                                 gitBranchName,
                                                 gitCommitObj)

        else:  # check for repeated commits make sure funciton is idempotent
            print('The states of the commit in branch "{0}" have already been added'.format(gitBranchName))  # noqa: E501
    else:
        print('The folder "{0}" is not found in commit {1}'.format(STATES_FOLDER,
                                                                   gitCommitObj.gitHash))

    return numStatesAdded


# get a Commit Object using a Commit SHA from database
def saveCommit(gitCommitSHA):
    # check if this commit is already in database
    if(Commit.objects.filter(gitHash=gitCommitSHA).count() <= 0):
        commitObj = Commit(gitHash=gitCommitSHA)
        commitObj.save()
        return commitObj
    else:
        return Commit.objects.get(gitHash=gitCommitSHA)


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

                # head of the Pull Request save branch name and commitSHA
                headRepoName = specificPR['head']['repo']['full_name']
                headBranchName = specificPR['head']['ref']
                headCommitObj = saveCommit(specificPR['head']['sha'])

                '''
                NOTE: this will add a row to the Commit table even if there are no states
                that are asssociated with the commit, storing unassociated Commit objects.
                Same with the base of the PR
                '''

                # Base of Pull Request save branch name and the commitSHA
                baseRepoName = specificPR['base']['repo']['full_name']
                baseBranchName = specificPR['base']['ref']
                baseCommitObj = saveCommit(specificPR['base']['sha'])

                print("Adding States: ")  # prompt user interface through terminal
                numStatesAdded = 0  # counts the number of states that have been added to data
                # save the json state representations into the database
                numStatesAdded += saveStates(headRepoName, headBranchName, headCommitObj)
                numStatesAdded += saveStates(baseRepoName, baseBranchName, baseCommitObj)

                # save information into the PR model
                gitPRNumber = specificPR['number']
                prObject = PR(gitRepo=baseRepoName,
                              gitPRNumber=gitPRNumber,
                              gitTargetCommit=baseCommitObj,
                              gitSourceCommit=headCommitObj)
                prObject.save()

                '''
                Add merged commit state into states table
                GITHUB API HAS NO MERGED_COMMIT_SHA UNTIL AFTER THE PR HAS BEEN CLOSED

                # Commit Hash of the Pull Request itself a merged version of head and base
                # The gitBRanch is the branch it will end up in after being merged(base)
                prCommitSHA = specificPR['merge_commit_sha']

                # Merged PR commit use the repo that the PR will end up in (base)
                numStatesAdded += saveStates(baseRepoName, baseBranchName, prCommitSHA)
                '''

                print("Successfully saved {0} new states".format(numStatesAdded))

            else:
                errorMessage = 'Could not retrieve PR {0} info from git repo'.format(prNumber)
        except State.DoesNotExist:
            raise CommandError(errorMessage)
