import os
from collections import defaultdict

import django_rq
from add_screenshots import add_screenshots
from HookCatcher.management.commands.functions.gen_diff import (gen_diff,
                                                                imagemagick)
from HookCatcher.models import Diff, History

RQ_QUEUE = django_rq.get_queue('default')


# override the commit objects for the PR with the latest commits
def new_commit_old_pr(pr_obj, new_base_states, new_head_states):
    import time
    start_time = time.time()
    img_pairs_dict = defaultdict(lambda: defaultdict(list))

    # map to a list of dicts to simply be able to determine where
    # a pair of images (old commit, new commit) of the same state and image settings is

    # WHERE key = head/base, state_name, browser_type, os, width, height
    # load all the old images first to the list
    for old_base_img in pr_obj.git_target_commit.get_images():
        key = "{0}{1}{2}{3}x{4}".format(old_base_img.state.state_name,
                                        old_base_img.browser_type,
                                        old_base_img.operating_system,  # {2}
                                        old_base_img.device_res_width,
                                        old_base_img.device_res_height)
        img_pairs_dict[key]['BASE'].append(old_base_img)
    for old_head_img in pr_obj.git_source_commit.get_images():
        key = "{0}{1}{2}{3}x{4}".format(old_head_img.state.state_name,
                                        old_head_img.browser_type,
                                        old_head_img.operating_system,  # {2}
                                        old_head_img.device_res_width,
                                        old_head_img.device_res_height)
        img_pairs_dict[key]['HEAD'].append(old_head_img)

    # load new images to the list
    for base_state in new_base_states:
        new_base_images = add_screenshots(base_state)
        for new_base_img in new_base_images:
            key = "{0}{1}{2}{3}x{4}".format(new_base_img.state.state_name,
                                            new_base_img.browser_type,
                                            new_base_img.operating_system,  # {2}
                                            new_base_img.device_res_width,
                                            new_base_img.device_res_height)
            img_pairs_dict[key]['BASE'].append(new_base_img)
    for head_state in new_head_states:
        new_head_states = add_screenshots(head_state)
        for new_head_img in new_head_states:
            key = "{0}{1}{2}{3}x{4}".format(new_head_img.state.state_name,
                                            new_head_img.browser_type,
                                            new_head_img.operating_system,  # {2}
                                            new_head_img.device_res_width,
                                            new_head_img.device_res_height)
            img_pairs_dict[key]['HEAD'].append(new_head_img)
    # img_pairs_dict = {'img_key': {'BASE': [<old_img>, <new_img>], 'HEAD': [,]}, 'img_key2'}
    # Next: generate necessary diffs. if old diffs are present transfer the approved status

    # Based on an imgKey, access (base and head) X (old and new commit) versions
    for img_key in img_pairs_dict:
        img_type = img_pairs_dict[img_key]
        # compare the old and new versions of the image
        for img_base_head in img_pairs_dict[img_key]:
            if len(img_type[img_base_head]) == 2:  # SUCCESS: only should be two old & new
                old_img_obj = img_type[img_base_head][0]
                new_img_obj = img_type[img_base_head][1]

                # check if there are any loading images preventing imagemagick call success
                if old_img_obj.image_rendered() and new_img_obj.image_rendered():
                    old_img_path = old_img_obj.get_image_location()
                    new_img_path = new_img_obj.get_image_location()

                    # make sure not to delete yourself if the two images are the same
                    if old_img_path != new_img_path:
                        imagemagick_result = imagemagick(old_img_path, new_img_path)
                        if imagemagick_result == 0:
                            # delete the no longer linked new image
                            print 'Deleting Redundant Image: {0} since it is equal to: {1}'.format(
                                  new_img_path, old_img_path)

                            if os.path.exists(new_img_path):
                                os.remove(new_img_path)
                                try:
                                    # delete recursively the parent dirs error when dir not empty
                                    os.removedirs(os.path.dirname(new_img_path))
                                except OSError:  # IGNORE: will error when parent dir is not empty
                                    pass
                            # use an existing local file for the new image
                            new_img_obj.img_file = old_img_obj.img_file
                            new_img_obj.save()
                # else if one of the images is rendering,
                # the callback function should handle this diffing

            # CORNER CASE: a new state was added to the new commit, that was not in the old commit
            elif len(img_type[img_base_head]) < 2:
                print('Found new states to track for the PR in the new commit')
            else:  # FAIL: multiple states with the same name were defined.
                msg = 'No Diff could be made. There were more than one state with the same name "{0}" in Branch "{1}". Please fix this.'.format(  # noqa: E501
                      old_img_obj.state.state_name,
                      old_img_obj.state.git_commit.git_branch)
                History.log_sys_error(pr_obj, msg)

        # Try to find an exisiting Diff obj with old images

        # if there exists a head and base for a image_key
        if len(img_type) == 2:
            # if there are old and new images for an image_key
            if len(img_type['BASE']) == 2 and len(img_type['HEAD']) == 2:
                # Index [0] is the old version of the image_obj [1] is new image_obj
                existing_diff = Diff.objects.filter(target_img=img_type['BASE'][0],
                                                    source_img=img_type['HEAD'][0])
                # there exists an old diff, copy info over to new diff
                if existing_diff.count() == 1:
                    if (img_type['BASE'][0].img_file == img_type['BASE'][1].img_file and
                       img_type['HEAD'][0].img_file == img_type['HEAD'][1].img_file):
                        old_diff_obj = existing_diff.get()
                        new_diff_obj = Diff(diff_img_file=old_diff_obj.diff_img_file,
                                            target_img=img_type['BASE'][1],
                                            source_img=img_type['HEAD'][1],
                                            diff_percent=old_diff_obj.diff_percent,
                                            is_approved=old_diff_obj.is_approved)
                        new_diff_obj.save()
                        print('A Duplicate Diff was found from previous commits on this PR. Approval coppied over')  # noqa: E501
                # For some reason in the past a diff was never generated when it could have ...
                # generate a new diff cuz for some reason there is no old diff object..
                elif existing_diff.count() < 1:
                    RQ_QUEUE.enqueue(gen_diff, img_type['BASE'][1], img_type['HEAD'][1])

                else:  # more than 1 exisiting diff returned...
                    msg = 'There is more than 1 Diff found for a pair of images: {0}'.format(existing_diff)  # noqa: E501
                    History.log_sys_error(pr_obj, msg)
            # if there is only 1 image for base/head aka Let's create a new diff
            elif len(img_type['BASE']) == 1 and len(img_type['HEAD']) == 1:
                RQ_QUEUE.enqueue(gen_diff, img_type['BASE'][0], img_type['HEAD'][0])

            # else: something went wrong internally? multiple states with same statename?
        # else Can't make diff without a head and base!
    print("--- %s seconds ---" % (time.time() - start_time))
