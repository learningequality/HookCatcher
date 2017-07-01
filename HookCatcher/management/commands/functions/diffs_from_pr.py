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

import sh
from add_pr_info import add_pr_info
from add_screenshots import add_screenshots
from django.conf import settings  # database dir
from django.core.management import call_command  # call newPR update command

WORKING_DIR = path.abspath(settings.WORKING_DIR)


def switchBranch(gitBranch):
    working_git_dir = path.abspath(path.join(WORKING_DIR, '.git'))

    sh.git('--git-dir', working_git_dir, '--work-tree',
           WORKING_DIR, 'checkout', gitBranch)


# arguments can either be: int(prNumber) or dict(payload)
def diffs_from_pr(prnumber_or_payload):
    # output the states that were added to the database
    savedStatesDict = add_pr_info(prnumber_or_payload)
    imgDict = defaultdict(list)  # {'key': [ImgObj1>, <ImgObj2>], 'key2': [...}
    for stateName in savedStatesDict:
        for singleState in savedStatesDict[stateName]:  # should run two times
            switchBranch(singleState.gitCommit.gitBranch)
            imgList = add_screenshots(singleState)
            for i in imgList:
                # key should proabbly also use stateName, but stateNames needs not change
                key = "{0}{1}{2}{3}x{4}".format(i.state.stateName,
                                                i.browserType,
                                                i.operatingSystem,  # {2}
                                                i.width,
                                                i.height)
                imgDict[key].append(i)
    # if there are any images
    if imgDict:
        print "Generating {0} Diff(s)".format(len(imgDict))
        for imgPair in imgDict:
            # the list associated to a key should be exactly 2 one for head one for branch
            # else it is invalid for generating a diff
            if len(imgDict[imgPair]) == 2:
                call_command('addImgDiff',
                             'imagemagick',
                             imgDict[imgPair][0].imgName,
                             imgDict[imgPair][1].imgName)

            elif len(imgDict[imgPair]) == 1:
                print ('State "{0}" is defined for Branch "{1}" but not the opposing Branch'.format(imgDict[imgPair][0].state.stateName,             # noqa: E501
                                                                                                    imgDict[imgPair][0].state.gitCommit.gitBranch))  # noqa: E501
            else:
                print ('There were more than one state with the same name "{0}" in Branch "{1}"'.format(imgDict[imgPair][0].state.stateName,             # noqa: E501
                                                                                                        imgDict[imgPair][0].state.gitCommit.gitBranch))  # noqa: E501
    else:
        print('There was no setting for which screenshots to generate, so none were generated')  # noqa: E501
        sys.exit(0)
