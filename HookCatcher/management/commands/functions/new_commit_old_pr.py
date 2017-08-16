import os
from collections import defaultdict

from add_screenshots import add_screenshots
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from HookCatcher.management.commands.functions.gen_diff import imagemagick


# simple check if the string is a url or a local image path
def is_url(img_file_name):
    validator = URLValidator()
    try:
        validator(img_file_name)
        return True
    except ValidationError:
        return False


# override the commit objects for the PR with the latest commits
def new_commit_old_pr(pr_obj, new_base_states, new_head_states):
    img_pairs_dict = defaultdict(list)

    # map to a list of dicts to simply be able to determine where
    # a pair of images (old commit, new commit) of the same state and image settings is

    # WHERE key = head/base, state_name, browser_type, os, width, height
    # load all the old images first to the list
    for old_base_img in pr_obj.git_target_commit.get_images():
        key = "BASE:{0}{1}{2}{3}x{4}".format(old_base_img.state.state_name,
                                             old_base_img.browser_type,
                                             old_base_img.operating_system,  # {2}
                                             old_base_img.device_res_width,
                                             old_base_img.device_res_height)
        img_pairs_dict[key].append(old_base_img)
    for old_head_img in pr_obj.git_source_commit.get_images():
        key = "HEAD:{0}{1}{2}{3}x{4}".format(old_head_img.state.state_name,
                                             old_head_img.browser_type,
                                             old_head_img.operating_system,  # {2}
                                             old_head_img.device_res_width,
                                             old_head_img.device_res_height)
        img_pairs_dict[key].append(old_head_img)

    # load new images to the list
    for base_state in new_base_states:
        new_base_images = add_screenshots(base_state)
        for new_base_img in new_base_images:
            key = "BASE:{0}{1}{2}{3}x{4}".format(new_base_img.state.state_name,
                                                 new_base_img.browser_type,
                                                 new_base_img.operating_system,  # {2}
                                                 new_base_img.device_res_width,
                                                 new_base_img.device_res_height)
            img_pairs_dict[key].append(new_base_img)
    for head_state in new_head_states:
        new_head_states = add_screenshots(head_state)
        for new_head_img in new_head_states:
            key = "HEAD:{0}{1}{2}{3}x{4}".format(new_head_img.state.state_name,
                                                 new_head_img.browser_type,
                                                 new_head_img.operating_system,  # {2}
                                                 new_head_img.device_res_width,
                                                 new_head_img.device_res_height)
            img_pairs_dict[key].append(new_head_img)

    # RESULT: img_pairs_dict = {'base_img1': [<old_img>, <new_img>], 'head_img1': ...}
    # generate necessary diffs if any new diffs were introduced
    print img_pairs_dict
    for img_versions in img_pairs_dict:
        if len(img_pairs_dict[img_versions]) == 2:  # SUCCESS: only should be two old & new
            # check if each of the images is saved as an url or local storage
            if is_url(img_pairs_dict[img_versions][0].img_file.name):
                old_img_path = img_pairs_dict[img_versions][0].img_file.name
            else:
                old_img_path = img_pairs_dict[img_versions][0].img_file.path
            if is_url(img_pairs_dict[img_versions][1].img_file.name):
                new_img_path = img_pairs_dict[img_versions][1].img_file.name
            else:
                new_img_path = img_pairs_dict[img_versions][1].img_file.path

            imagemagick_result = imagemagick(old_img_path, new_img_path)
            if imagemagick_result is not None and imagemagick_result == 0:
                # delete the no longer linked new image
                print 'deleteing image %s' % new_img_path
                if os.path.exists(new_img_path):
                    os.remove(new_img_path)
                    try:
                        # delete recursively the parent dirs raises error when dir not empty
                        os.removedirs(os.path.dirname(new_img_path))
                    except OSError:  # will raise error when parent is not empty so just ignore this
                        pass
                img_pairs_dict[img_versions][0].img_file = img_pairs_dict[img_versions][1].img_file

            # if the diff_percent is > 0 then just do nothing because we want
            # new commit to simply override data of the pr

        elif len(img_pairs_dict[img_versions]) < 2:  # FAIL: a new state was added to the new commit
            print('No Diff could be made. State "{0}" is defined for Branch "{1}" but not the opposing Branch. Please fix this.'.format(  # noqa: E501
                  img_pairs_dict[img_versions][0].state.state_name,
                  img_pairs_dict[img_versions][0].state.git_commit.git_branch))
        else:  # FAIL: multiple states with the same name were defined.
            print('No Diff could be made. There were more than one state with the same name "{0}" in Branch "{1}". Please fix this.'.format(  # noqa: E501
                  img_pairs_dict[img_versions][0].state.state_name,
                  img_pairs_dict[img_versions][0].state.git_commit.git_branch))
