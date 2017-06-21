import json
from collections import defaultdict

import requests
from django.conf import settings  # database dir
from django.core.management.base import CommandError
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
        print('Adding State: {0}'.format(s))
        return s

    else:
        CommandError('There was no json files within the folder {0}'.format(STATES_FOLDER))

    return None


# Pass in the information about the PR
# Access the state JSON files and saving data into models
def saveStates(gitRepoName, gitBranchName, gitCommitObj):
    # initialize list of state obj
    stateObjList = []

    # get the directory of the states folder with the JSON states
    statesDir = '{0}?ref={1}'.format(STATES_FOLDER, gitCommitObj.gitHash)
    # example url
    gitContentURL = '{0}/contents/{1}'.format(GIT_REPO_API, statesDir)
    reqStatesList = requests.get(gitContentURL, headers=GIT_HEADER)

    if (reqStatesList.status_code == 200):
        gitStatesList = json.loads(reqStatesList.text)
        # if stateList = 0, then exit as well because there are no states to add
        # if the states of this commit has already been added to database then don't add it again

        # filter gitHash first
        if(State.objects.filter(gitCommit=gitCommitObj).count() < len(gitStatesList)):
            # save the json content for each file of the STATES_FOLDER defined in user_settings
            for eachState in gitStatesList:
                stateObjList.append(parseStateJSON(eachState,
                                                   gitRepoName,
                                                   gitBranchName,
                                                   gitCommitObj))
        else:  # check for repeated commits make sure funciton is idempotent

            CommandError('States of commit "{0}" have already been added'.format(gitCommitObj.gitHash[:7]))  # noqa: E501
    else:
        CommandError('Folder "{0}" was not found in commit {1}'.format(STATES_FOLDER,
                                                                       gitCommitObj.gitHash[:7]))
    return stateObjList


# get a Commit Object using a Commit SHA from database
def saveCommit(gitCommitSHA):
    # check if this commit is already in database
    if(Commit.objects.filter(gitHash=gitCommitSHA).count() <= 0):
        commitObj = Commit(gitHash=gitCommitSHA)
        commitObj.save()
        print('Adding states of new commit "{0}"'.format(gitCommitSHA[:7]))
        return commitObj
    else:
        return Commit.objects.get(gitHash=gitCommitSHA)


def addPRinfo(prNumber):
    # get the information about a certain PR through Github API
    gitPullURL = '{0}/pulls/{1}'.format(GIT_REPO_API, prNumber)
    reqSpecificPR = requests.get(gitPullURL, headers=GIT_HEADER)
    # make sure connection to Github API was successful
    if (reqSpecificPR.status_code == 200):
        print('Accessing "{0}"'.format(gitPullURL))
        specificPR = json.loads(reqSpecificPR.text)

        # Base of Pull Request save branch name and the commitSHA
        baseRepoName = specificPR['base']['repo']['full_name']
        baseBranchName = specificPR['base']['ref']
        baseCommitObj = saveCommit(specificPR['base']['sha'])

        '''
        NOTE: this will add a row to the Commit table even if there are no states
        that are asssociated with the commit, storing unassociated Commit objects.
        Same with the base of the PR

        '''
        # head of the Pull Request save branch name and commitSHA
        headRepoName = specificPR['head']['repo']['full_name']
        headBranchName = specificPR['head']['ref']
        headCommitObj = saveCommit(specificPR['head']['sha'])

        saveStates(baseRepoName, baseBranchName, baseCommitObj)
        saveStates(headRepoName, headBranchName, headCommitObj)

        # returns a dictionary of states that were added {'stateName1': (baseVers, headVers), ...}
        # this list is to be sent to screenshot generator to be taken screenshot of
        newStatesDict = defaultdict(list)

        baseStatesList = State.objects.filter(gitRepo=baseRepoName,
                                              gitBranch=baseBranchName,
                                              gitCommit=baseCommitObj)

        # save the json state representations into the database and add added states to list
        headStatesList = State.objects.filter(gitRepo=headRepoName,
                                              gitBranch=headBranchName,
                                              gitCommit=headCommitObj)

        # key is url because devs can make mistake of changing state name
        # if url changes betweeen state versions then need way of shared identifier
        for stateObjB in baseStatesList:
            newStatesDict[stateObjB.stateUrl].append(stateObjB)

        for stateObjH in headStatesList:
            # {'key' : baseStateObj, headStateObj, "key"}
            newStatesDict[stateObjH.stateUrl].append(stateObjH)

        # Add merged pr commit state into states table
        # GITHUB API HAS NO MERGED_COMMIT_SHA WHEN FIRST OPENED
        prCommitObj = None
        # check if there is a hash for the merged commit of a pr
        if(specificPR['merge_commit_sha']):
            prCommitObj = saveCommit(specificPR['merge_commit_sha'])

            # Merged PR commit use the repo that the PR will end up in (base)
            # not sure how to take screenshot of this so not included in saveStates List
            saveStates(baseRepoName, baseBranchName, prCommitObj)

        gitPRNumber = specificPR['number']
        # Update an entry when the merged pr commit hash now exists on Git
        if(PR.objects.filter(gitPRNumber=gitPRNumber).count() > 0):
            prObject = PR.objects.get(gitPRNumber=gitPRNumber)  # get existing pr entry
            # check if the pr commit is different from the previous
            if (prObject.gitPRCommit != prCommitObj):
                prObject.gitPRCommit = prCommitObj
                prObject.save()
                print("Successfully updated PR {0}".format(gitPRNumber))

        else:  # there is no merge_commit_sha for a newly opened PR
            # save information into the PR model
            prObject = PR(gitRepo=baseRepoName,
                          gitPRNumber=gitPRNumber,
                          gitTargetCommit=baseCommitObj,
                          gitSourceCommit=headCommitObj,
                          gitPRCommit=prCommitObj)
            prObject.save()
            print("Successfully added PR {0}".format(gitPRNumber))

        print("Saved new states")

        return newStatesDict  # {'statename': (headObj, baseObj), 'statename1'...}

    else:
        CommandError('Could not retrieve PR {0} info from git repo'.format(prNumber))
