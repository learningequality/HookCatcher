'''
        Desired output ->
        1. Relevant git Commits and PR information is added to our tables
        2. images are taken for all new states BUT NOT FOR PREXISTING STATES THAT HAVE IMAGES
        3. Diffs are generated for all pairs of images that can be diffed

        ~ If no states are even checked in, do nothing.
        ~ if PR number isn''t valid, do nothing
'''
import sys
from collections import defaultdict
from os import path

import django_rq
import requests
import sh
import time
from add_pr_info import add_pr_info
from add_screenshots import add_screenshots
from django.conf import settings  # database dir
from HookCatcher.management.commands.functions.gen_diff import gen_diff
from rq import Queue, Connection, Worker
from redis import Redis


WORKING_DIR = path.abspath(settings.WORKING_DIR)


def switchBranch(gitBranch):
    working_git_dir = path.abspath(path.join(WORKING_DIR, '.git'))

    sh.git('--git-dir', working_git_dir, '--work-tree',
           WORKING_DIR, 'checkout', gitBranch)


# parrallel processes for each stateName from here
        # input: A single stateName
        # Output: Screenshots for all states, All diffs possible
        # Edge: Can be 0 diffs generated 
def generateFromState(stateName):
    imgDict = defaultdict(list)  # {'key': [ImgObj1>, <ImgObj2>], 'key2': [...}
    for singleState in stateName:  # should run two times
        # switchBranch(singleState.git_commit.git_branch) # depricate
        imgList = add_screenshots(singleState)

        for i in imgList:
            # key uniquely identifies a diffable screenshot
            key = "{0}{1}{2}{3}x{4}".format(i.state.state_name,
                                            i.browser_type,
                                            i.operating_system,  # {2}
                                            i.device_res_width,
                                            i.device_res_height)
            imgDict[key].append(i)
        # if there are any images
        if imgDict:
            print ''  # separating delinate diffs from others
            for imgPair in imgDict:
                # the list associated to a key should be exactly 2 one for head one for branch
                # else it is invalid for generating a diff
                if len(imgDict[imgPair]) == 2:
                    gen_diff('imagemagick',
                             imgDict[imgPair][0].img_file.name,
                             imgDict[imgPair][1].img_file.name)
                elif len(imgDict[imgPair]) == 1:
                    print ('No Diff could be made. State "{0}" is defined for Branch "{1}" but not the opposing Branch. Please fix this.'.format(imgDict[imgPair][0].state.state_name,             # noqa: E501
                                                                                                        imgDict[imgPair][0].state.git_commit.git_branch))  # noqa: E501
                else:
                    print ('No Diff could be made. There were more than one state with the same name "{0}" in Branch "{1}". Please fix this.'.format(imgDict[imgPair][0].state.state_name,             # noqa: E501
                                                                                                            imgDict[imgPair][0].state.git_commit.git_branch))  # noqa: E501
        else:
            print('There was no setting for which screenshots to generate, so none were generated')  # noqa: E501


# arguments can either be: int(prNumber) or dict(payload)
def diffs_from_pr(prnumber_or_payload):
    start_time = time.time()

    # output the states that were added to the database
    savedStatesDict = add_pr_info(prnumber_or_payload)
    for stateName in savedStatesDict:
        # generateFromState(savedStatesDict[stateName])

        queue = django_rq.get_queue('default')

        job = queue.enqueue(generateFromState, savedStatesDict[stateName])
        print queue
    print('Completed all tasks')
    print("--- %s seconds ---" % (time.time() - start_time))
