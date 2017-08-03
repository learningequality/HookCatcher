'''
        Desired output ->
        1. Relevant git Commits and PR information is added to our tables
        2. images are taken for all new states BUT NOT FOR PREXISTING STATES THAT HAVE IMAGES
        3. Diffs are generated for all pairs of images that can be diffed

        ~ If no states are even checked in, do nothing.
        ~ if PR number isn''t valid, do nothing
'''
from collections import defaultdict
from os import path

import django_rq
import sh

from add_pr_info import add_pr_info
from add_screenshots import add_screenshots
from django.conf import settings  # database dir
from HookCatcher.management.commands.functions.gen_diff import gen_diff

from HookCatcher.models import Diff


WORKING_DIR = path.abspath(settings.WORKING_DIR)
RQ_QUEUE = django_rq.get_queue('default')


def switchBranch(gitBranch):
    working_git_dir = path.abspath(path.join(WORKING_DIR, '.git'))

    sh.git('--git-dir', working_git_dir, '--work-tree',
           WORKING_DIR, 'checkout', gitBranch)


# Helper method to check if the image is currently loading or not. Return True if loaded
def img_loaded(img_file):
    return not img_file == None and not img_file.name == ''  # noqa: E711


def generate_diffs(img_dict):
    for img_pair in img_dict:
        # the list associated to a key should be exactly 2 one for head one for branch
        # else it is invalid for generating a diff
        if len(img_dict[img_pair]) == 2:
            if (not img_loaded(img_dict[img_pair][0].img_file) or
               not img_loaded(img_dict[img_pair][1].img_file)):
                temp_diff = Diff(target_img=img_dict[img_pair][0], source_img=img_dict[img_pair][1])
                temp_diff.save()
            else:
                gen_diff(img_dict[img_pair][0].img_file.name,
                         img_dict[img_pair][1].img_file.name)

        elif len(img_dict[img_pair]) == 1:
            print('No Diff could be made. State "{0}" is defined for Branch "{1}" but not the opposing Branch. Please fix this.'.format(  # noqa: E501
                  img_dict[img_pair][0].state.state_name,
                  img_dict[img_pair][0].state.git_commit.git_branch))
        else:
            print('No Diff could be made. There were more than one state with the same name "{0}" in Branch "{1}". Please fix this.'.format(  # noqa: E501
                  img_dict[img_pair][0].state.state_name,
                  img_dict[img_pair][0].state.git_commit.git_branch))
    return


# parrallel processes for each stateName from here
    # input: A single stateName
    # Output: Screenshots for all states, All diffs possible
    # Edge: Can be 0 diffs generated
def generate_images(state_name):
    img_dict = defaultdict(list)  # {'key': [<ImgObj1>, <ImgObj2>], 'key2': [...}
    for single_state in state_name:  # should run two times
        # switchBranch(singleState.git_commit.git_branch) # depricate

        img_list = add_screenshots(single_state)

        for i in img_list:
            # key uniquely identifies a diffable screenshot
            key = "{0}{1}{2}{3}x{4}".format(i.state.state_name,
                                            i.browser_type,
                                            i.operating_system,  # {2}
                                            i.device_res_width,
                                            i.device_res_height)
            img_dict[key].append(i)

    # if there are any images
    if img_dict:
        RQ_QUEUE.enqueue(generate_diffs, img_dict)
    else:
        print('There was no setting for which screenshots to generate, so none were generated')  # noqa: E501
    return


# arguments can either be: int(prNumber) or dict(payload)
def diffs_from_pr(prnumber_or_payload):
    # output the states that were added to the database
    savedStatesDict = add_pr_info(prnumber_or_payload)
    for stateName in savedStatesDict:
        # generateFromState(savedStatesDict[stateName])
        RQ_QUEUE.enqueue(generate_images, savedStatesDict[stateName])

    print('Completed all tasks')
