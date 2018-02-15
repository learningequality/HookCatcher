import json
import logging
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
# Logger variable to record such things
LOGGER = logging.getLogger(__name__)


# Read a single json file that represents a state and save into models
# save the commit object into the database
# reutrn true if successfully added new state, false else
def parseStateJSON(stateRepresentation, git_commit_obj, pr_obj):
    # get the raw json file for each state
    rawURL = stateRepresentation["download_url"]
    reqRawState = requests.get(rawURL, headers=GIT_HEADER)
    state_obj = None
    try:
        # save the json as a regular string
        rawState = json.loads(reqRawState.text)
        state_obj = State(state_name=rawState['name'],
                          state_desc=rawState['description'],
                          state_url=rawState['url'],
                          git_commit=git_commit_obj)
    except ValueError:
        return False
    # Specific implementation that sets entered username & password with host url.
    try:
        state_obj.login_username = rawState['username']
        state_obj.login_password = rawState['password']
    except KeyError:
        pass
    state_obj.save()
    LOGGER.debug('Adding State: {0}'.format(state_obj))
    return True


# Pass in the information about the PR
# Access the state JSON files and saving data into models
def saveStates(git_commit_obj, pr_obj):
    # get the directory of the states folder with the JSON states
    statesDir = '{0}?ref={1}'.format(STATES_FOLDER, git_commit_obj.git_hash)
    # example url https://api.github.com/repos/MingDai/kolibri/contents/states?ref=b5f089b
    gitContentURL = '{0}/contents/{1}'.format(GIT_REPO_API, statesDir)

    reqStatesList = requests.get(gitContentURL, headers=GIT_HEADER)

    num_added_states = 0
    num_error_states = 0
    if (reqStatesList.status_code == 200):
        gitStatesList = json.loads(reqStatesList.text)

        # if stateList = 0, then exit as well because there are no states to add
        # if the states of this commit has already been added to database then don't add it again
        # ASSUMPTION, requires a new commit to change a state's JSON
        if(State.objects.filter(git_commit=git_commit_obj).count() < len(gitStatesList)):
            # save the json content for each file of the STATES_FOLDER defined in user_settings
            for eachState in gitStatesList:
                if parseStateJSON(eachState, git_commit_obj, pr_obj):
                    num_added_states += 1
                else:
                    num_error_states += 1

            if num_error_states > 0:
                msg = 'There are {0} improperly formatted json files within the folder "{1}" on commit {2}'.format(num_error_states,  # noqa: E501
                                                                                                                   STATES_FOLDER,  # noqa: E501
                                                                                                                   git_commit_obj.git_hash[:7])  # noqa: E501
                LOGGER.error(msg)
                History.log_sys_error(pr_obj, msg)
            if num_added_states > 0:
                msg = 'Added {0} states to commit "{1}"'.format(num_added_states, git_commit_obj.git_hash[:7])  # noqa: E501
                LOGGER.debug(msg)

        else:  # check for repeated commits make sure funciton is idempotent
            LOGGER.debug('States of commit "{0}" have already been added'.format(git_commit_obj.git_hash[:7]))  # noqa: E501
    else:
        msg = 'A folder of states "{0}" was not found in branch "{1}" commit "{2}"'.format(STATES_FOLDER,              # noqa: E501
                                                                                           git_commit_obj.git_branch,     # noqa: E501
                                                                                           git_commit_obj.git_hash[:7])  # noqa: E501
        LOGGER.critical(msg)
        History.log_sys_error(pr_obj, msg)

    if num_error_states:
        return False
    else:
        return True


# get a Commit Object using a Commit SHA from database
def saveCommit(gitRepoName, gitBranchName, gitCommitSHA):
    commitObj, is_new = Commit.objects.get_or_create(git_repo=gitRepoName,
                                                     git_branch=gitBranchName,
                                                     git_hash=gitCommitSHA)
    if is_new:
        LOGGER.debug('Adding new commit "{0}"'.format(gitCommitSHA[:7]))
    return commitObj


# usually is called through webhookHandler management command
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
            LOGGER.debug('Accessing "{0}"'.format(gitPullURL))
            specificPR = json.loads(reqSpecificPR.text)
        else:
            LOGGER.critical('Could not retrieve PR {0} from your git Repository'.format(prNumber))
            sys.exit(0)
    elif isinstance(prnumber_payload, dict):
        specificPR = prnumber_payload
    else:
        # exit out of the whole function
        LOGGER.critical('Invalid payload')
        sys.exit(0)

    # Base of Pull Request save branch name and the commitSHA
    baseRepoName = specificPR['base']['repo']['full_name']
    baseBranchName = specificPR['base']['ref']
    baseCommitObj = saveCommit(baseRepoName, baseBranchName, specificPR['base']['sha'])

    '''
    NOTE: this will add a row to the Commit table even if there are no states
    that are asssociated with the commit, storing potentially unassociated Commit objects.
    '''

    # head of the Pull Request save branch name and commitSHA
    headRepoName = specificPR['head']['repo']['full_name']
    headBranchName = specificPR['head']['ref']
    headCommitObj = saveCommit(headRepoName, headBranchName, specificPR['head']['sha'])

    # TODO: is this an assumption? specificPR['number'])[0]
    pr_object = PR.objects.get_or_create(git_repo=baseRepoName,
                                         git_title=specificPR['title'],
                                         git_pr_number=specificPR['number'])[0]
    LOGGER.info('Saving Github metadata for Pull Request #{0}'.format(specificPR['number'])[0])

    # Single Source of Truth of which build is newest-> time PR was changed from Github
    # github has a time listed for when this commit was updated to trigger this event
    last_updated = datetime.strptime(specificPR['updated_at'], "%Y-%m-%dT%H:%M:%SZ")

    build_object = Build.objects.get_or_create(pr=pr_object,
                                               pr_version=len(pr_object.build_set.all()),
                                               date_time=last_updated,
                                               git_target_commit=baseCommitObj,
                                               git_source_commit=headCommitObj)[0]

    ERROR_BUILD_STATUS_CODE = 4  # to show the build has some issues with it

    # Search Git for the 'states' folders and if they exist, save those states to database
    if saveStates(baseCommitObj, pr_object) is False:
        build_object.status_code = ERROR_BUILD_STATUS_CODE
        build_object.save()

    if saveStates(headCommitObj, pr_object) is False:
        build_object.status_code = ERROR_BUILD_STATUS_CODE
        build_object.save()
