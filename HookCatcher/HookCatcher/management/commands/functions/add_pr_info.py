import json
import sys
from datetime import datetime

import requests
from django.conf import settings  # database dir
from HookCatcher.models import PR, Build, Commit, History, State

STATES_FOLDER = settings.STATES_FOLDER  # folder within git repo that organizes the list of states

# header of the git GET request
GIT_HEADER = {
    'Authorization': 'token ' + settings.GIT_OAUTH,
}

# GIT_REPO_API example form "https://api.github.com/repos/MingDai/kolibri"
GIT_REPO_API = 'https://api.github.com/repos/{0}'.format(settings.GIT_REPO)


# Read a single json file that represents a state and save into models
# save the commit object into the database
def parseStateJSON(stateRepresentation, git_commit_obj, pr_obj):
    # get the raw json file for each state
    rawURL = stateRepresentation["download_url"]
    reqRawState = requests.get(rawURL, headers=GIT_HEADER)
    try:
        # save the json as a regular string
        rawState = json.loads(reqRawState.text)
        state_obj = State(state_name=rawState['name'],
                          state_desc=rawState['description'],
                          state_url=rawState['url'],
                          git_commit=git_commit_obj)
    except ValueError:
        msg = 'There are improperly formatted json files within the folder "{0}"'.format(STATES_FOLDER)  # noqa: E501
        print msg
        History.log_sys_error(pr_obj, msg)

    if state_obj:
        try:
            state_obj.login_username = rawState['username']
            state_obj.login_password = rawState['password']
        except KeyError:
            pass
        state_obj.save()
        print('Adding State: {0}'.format(state_obj))
        return state_obj
    return None


# Pass in the information about the PR
# Access the state JSON files and saving data into models
def saveStates(git_commit_obj, pr_obj):
    # initialize list of state obj
    stateObjList = []

    # get the directory of the states folder with the JSON states
    statesDir = '{0}?ref={1}'.format(STATES_FOLDER, git_commit_obj.git_hash)
    # example url https://api.github.com/repos/MingDai/kolibri/contents/states?ref=b5f089b
    gitContentURL = '{0}/contents/{1}'.format(GIT_REPO_API, statesDir)

    reqStatesList = requests.get(gitContentURL, headers=GIT_HEADER)

    if (reqStatesList.status_code == 200):
        gitStatesList = json.loads(reqStatesList.text)
        # if stateList = 0, then exit as well because there are no states to add
        # if the states of this commit has already been added to database then don't add it again

        # filter gitHash first
        if(State.objects.filter(git_commit=git_commit_obj).count() < len(gitStatesList)):
            # save the json content for each file of the STATES_FOLDER defined in user_settings
            for eachState in gitStatesList:
                new_state = parseStateJSON(eachState, git_commit_obj, pr_obj)
                if new_state:
                    stateObjList.append(new_state)
        else:  # check for repeated commits make sure funciton is idempotent
            print('States of commit "{0}" have already been added'.format(git_commit_obj.git_hash[:7]))  # noqa: E501
    else:
        msg = 'A folder of states "{0}" was not found in branch "{1}" commit "{2}"'.format(STATES_FOLDER,              # noqa: E501
                                                                                         git_commit_obj.git_branch,     # noqa: E501
                                                                                         git_commit_obj.git_hash[:7])  # noqa: E501
        print msg
        History.log_sys_error(pr_obj, msg)
        return False
    return stateObjList


# get a Commit Object using a Commit SHA from database
def saveCommit(gitRepoName, gitBranchName, gitCommitSHA):
    # check if this commit is already in database
    if(Commit.objects.filter(git_repo=gitRepoName,
                             git_branch=gitBranchName,
                             git_hash=gitCommitSHA).count() <= 0):
        commitObj = Commit(git_repo=gitRepoName, git_branch=gitBranchName, git_hash=gitCommitSHA)
        commitObj.save()
        print('Adding new commit "{0}"'.format(gitCommitSHA[:7]))
        return commitObj
    else:
        return Commit.objects.get(git_repo=gitRepoName,
                                  git_branch=gitBranchName,
                                  git_hash=gitCommitSHA)


# arguments can either be: int(prNumber) or dict(payload)
def add_pr_info(prnumber_payload):
    # function called: addPRinfo(prNumber)
    if isinstance(prnumber_payload, int):
        prNumber = prnumber_payload
        # ex: https://api.github.com/repos/MingDai/kolibri/pulls/22
        # get the information about a certain PR through Github API using PR number
        gitPullURL = '{0}/pulls/{1}'.format(GIT_REPO_API, prNumber)
        reqSpecificPR = requests.get(gitPullURL, headers=GIT_HEADER)
        # make sure connection to Github API was successful
        if (reqSpecificPR.status_code == 200):
            print('Accessing "{0}"'.format(gitPullURL))
            specificPR = json.loads(reqSpecificPR.text)
        else:
            print('Could not retrieve PR {0} from your git Repository'.format(prNumber))
            sys.exit(0)
    elif isinstance(prnumber_payload, dict):
        specificPR = prnumber_payload
    else:
        # exit out of the whole function
        print('Invalid payload')
        sys.exit(0)

    # Base of Pull Request save branch name and the commitSHA
    baseRepoName = specificPR['base']['repo']['full_name']
    baseBranchName = specificPR['base']['ref']
    baseCommitObj = saveCommit(baseRepoName, baseBranchName, specificPR['base']['sha'])

    '''
    NOTE: this will add a row to the Commit table even if there are no states
    that are asssociated with the commit, storing unassociated Commit objects.
    Same with the base of the PR

    '''

    # head of the Pull Request save branch name and commitSHA
    headRepoName = specificPR['head']['repo']['full_name']
    headBranchName = specificPR['head']['ref']
    headCommitObj = saveCommit(headRepoName, headBranchName, specificPR['head']['sha'])

    last_updated = datetime.strptime(specificPR['updated_at'], "%Y-%m-%dT%H:%M:%SZ")

    # if this PR already exists in the database yet
    if (PR.objects.filter(git_pr_number=specificPR['number']).count() > 0):
        pr_object = PR.objects.get(git_pr_number=specificPR['number'])
        # check if the build with these commits on this PR already exists
        find_build = Build.objects.filter(pr=pr_object,
                                          git_target_commit=baseCommitObj,
                                          git_source_commit=headCommitObj)
        # This exact build already exists
        if find_build.count() > 0:
            build_object = find_build.get()
        else:
            build_object = Build(pr=pr_object,
                                 pr_version=len(pr_object.build_set.all()),
                                 date_time=last_updated,
                                 git_target_commit=baseCommitObj,
                                 git_source_commit=headCommitObj)
            build_object.save()
    else:
        pr_object = PR(git_repo=baseRepoName,
                       git_title=specificPR['title'],
                       git_pr_number=specificPR['number'])
        pr_object.save()

        build_object = Build(pr=pr_object,
                             pr_version=len(pr_object.build_set.all()),
                             date_time=last_updated,
                             git_target_commit=baseCommitObj,
                             git_source_commit=headCommitObj)
        build_object.save()

    if saveStates(baseCommitObj, pr_object) is False:
        build_object.status_code = 4  # error code for build
        build_object.save()

    if saveStates(headCommitObj, pr_object) is False:
        build_object.status_code = 4  # error code for build
        build_object.save()
    return


'''
REST OF THIS IS DEPRECATED FROM NEW_COMMIT_OLD_PR

return nothing

    # returns a dictionary of states that were added {'stateName1': (baseVers, headVers), ...}
    # this list is to be sent to screenshot generator to be taken screenshot of
    newStatesDict = defaultdict(list)
    baseStatesList = State.objects.filter(git_commits=baseCommitObj)
    # save the json state representations into the database and add added states to list
    headStatesList = State.objects.filter(git_commit=headCommitObj)

    # key is state_name because a single state may have two different urls depending on version
    # if people name the state wrong this can cause errors in the system
    for stateObjB in baseStatesList:
        newStatesDict[stateObjB.state_name].append(stateObjB)
    for stateObjH in headStatesList:
        # {'key' : baseStateObj, headStateObj, 'key': ...}
        newStatesDict[stateObjH.state_name].append(stateObjH)

    # if this PR doesn't exist in the database yet
    if(PR.objects.filter(git_pr_number=specificPR['number']).count() > 0):
        old_pr_object = PR.objects.get(git_pr_number=specificPR['number'])
        if (baseCommitObj.git_hash != old_pr_object.git_target_commit.git_hash or
           headCommitObj.git_hash != old_pr_object.git_source_commit.git_hash):
            print('New changes detected in PR #{0} Git Repo: "{1}/{2}"'.format(specificPR['number'],
                                                                               baseRepoName,
                                                                               baseBranchName))

            new_commit_old_pr(old_pr_object, baseStatesList, headStatesList)
            old_pr_object.git_target_commit = baseCommitObj
            old_pr_object.git_source_commit = headCommitObj
            old_pr_object.save()
            # new_commit_old_pr already handles all the logic needed so don't go to diffs from pr
            sys.exit(0)
        else:  # do nothing because this is just a repeated call to a PR that didnt change
            print('PR #{0} for Github Repo: "{1}/{2}" already exists'.format(specificPR['number'],
                                                                             baseRepoName,
                                                                             baseBranchName))
    else:  # absolutely new PR is being added to models
        # save information into the PR model
        print("Successfully added PR {0}".format(specificPR['number']))

    # newStatesDict = {'statename': (headObj, baseObj), 'statename1'...}
    return {'states_list': newStatesDict, 'pr_object': pr_object, 'build_object': build_object}
'''
