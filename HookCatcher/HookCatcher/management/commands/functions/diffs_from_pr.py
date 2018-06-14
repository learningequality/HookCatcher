'''
        Desired output ->
        1. Relevant git Commits and PR information is added to our tables
        2. images are taken for all new states BUT NOT FOR PREXISTING STATES THAT HAVE IMAGES
        3. Diffs are generated for all pairs of images that can be diffed

        ~ If no states are even checked in, do nothing.
        ~ if PR number isn''t valid, do nothing
'''
import logging
import os
import time
from collections import defaultdict

import django_rq
from channels import Group
from HookCatcher.management.commands.functions.add_screenshots import \
  add_screenshots
from HookCatcher.management.commands.functions.gen_diff import (gen_diff,
                                                                imagemagick)
from HookCatcher.models import Build, Diff, History

RQ_QUEUE = django_rq.get_queue('default')
LOGGER = logging.getLogger(__name__)


UNINITIATED_BUILD_STATUS_CODE = 0
IN_PROGRESS_BUILD_STATUS_CODE = 1
COMPLETED_BUILD_STATUS_CODE = 2
CANCELLED_BUILD_STATUS_CODE = 3
ERROR_BUILD_STATUS_CODE = 4


def is_int(var):
    try:
        int(var)
    except TypeError:  # not an int
        return False
    return True


# img_pairs_dict holds the new images for new commit going into this function
def transfer_old_build_data_to_new_build(img_pairs_dict, old_build):
    # add old images to img_pairs_dict
    for old_base_img in old_build.git_target_commit.get_images():
        key = "{0}{1}{2}{3}x{4}".format(old_base_img.state.state_name,
                                        old_base_img.browser_type,
                                        old_base_img.operating_system,  # {2}
                                        old_base_img.device_res_width,
                                        old_base_img.device_res_height)
        img_pairs_dict[key]['BASE'].append(old_base_img)
    for old_head_img in old_build.git_source_commit.get_images():
        key = "{0}{1}{2}{3}x{4}".format(old_head_img.state.state_name,
                                        old_head_img.browser_type,
                                        old_head_img.operating_system,  # {2}
                                        old_head_img.device_res_width,
                                        old_head_img.device_res_height)
        img_pairs_dict[key]['HEAD'].append(old_head_img)
    # calculate to see if there are differences between images of new build vs old build
    # if not, use the old image file that already exists and transfer over approval status
    for img_key in img_pairs_dict:
        img_type = img_pairs_dict[img_key]
        # compare the old and new versions of the image
        for img_base_head in img_pairs_dict[img_key]:
            if len(img_type[img_base_head]) == 2:  # SUCCESS: only should be two old & new
                old_img_obj = img_type[img_base_head][0]
                new_img_obj = img_type[img_base_head][1]

                # check if there are any loading images preventing imagemagick call success
                if old_img_obj.img_file and new_img_obj.img_file:
                    old_img_path = old_img_obj.get_location()
                    new_img_path = new_img_obj.get_location()

                    # Delete a redundant image same image saved in different locations
                    # make sure not to delete yourself if the two images are the same
                    if old_img_path != new_img_path:
                        imagemagick_result = imagemagick(old_img_obj, new_img_obj)
                        if imagemagick_result == 0:
                            # delete the no longer linked new image
                            LOGGER.info('Deleting Redundant Image: {0} since it is equal to: {1}'.format(  # noqa: E501
                                        new_img_path, old_img_path))

                            if os.path.exists(new_img_path):
                                os.remove(new_img_path)
                                try:
                                    # delete recursively the parent dirs error when dir not empty
                                    os.removedirs(os.path.dirname(new_img_path))
                                except OSError:  # IGNORE: will error when parent dir is not empty
                                    pass
                            # use an old local file location and approve values for the new image
                            new_img_obj.img_file = old_img_obj.img_file
                            new_img_obj.is_approved = old_img_obj.is_approved
                            new_img_obj.save()
                # else if one of the screenshot images is still rendering,
                # the callback function should handle this diffing


def generate_diffs(img_type, build_obj):
    if len(img_type) == 2:  # {type: {HEAD, BASE}}
        # if there are old and new images for base and head of an image_key
        if len(img_type['BASE']) == 2 and len(img_type['HEAD']) == 2:
            # img_type['BASE']<Index [0]> is the new version of the image_obj,
                            # <Index [1]> is the old image_obj
            existing_diff = Diff.objects.filter(target_img=img_type['BASE'][1],
                                                source_img=img_type['HEAD'][1])
            # there exists an old diff, copy info over to new diff
            if existing_diff.count() == 1:
                # image file of base[0] and base[1] are identical
                if (img_type['BASE'][0].img_file == img_type['BASE'][1].img_file and
                   img_type['HEAD'][0].img_file == img_type['HEAD'][1].img_file):
                    old_diff_obj = existing_diff.get()
                    new_diff_obj = Diff(diff_img_file=old_diff_obj.diff_img_file,
                                        target_img=img_type['BASE'][0],
                                        source_img=img_type['HEAD'][0],
                                        diff_percent=old_diff_obj.diff_percent,
                                        is_approved=old_diff_obj.is_approved)
                    new_diff_obj.save()
                    LOGGER.debug('A Duplicate Diff was found from previous commits on this PR. Approval coppied over')  # noqa: E501
            # For some reason in the past a diff was never generated when it could have ...
            # generate a new diff cuz for some reason there is no old diff object..
            # doesn't try to change old build to have a diff object
            elif existing_diff.count() < 1:
                gen_diff(img_type['BASE'][0], img_type['HEAD'][0])

            else:  # more than 1 exisiting diff returned...
                msg = 'There is more than 1 Diff found for a pair of images: {0}'.format(existing_diff)  # noqa: E501
                History.log_sys_error(build_obj.pr, msg)
        # if there is only 1 image for base/head aka Let's create a new diff
        elif len(img_type['BASE']) == 1 and len(img_type['HEAD']) == 1:
            gen_diff(img_type['BASE'][0], img_type['HEAD'][0])
    # ELIF len(img_type) == 1:
    # There is a new or deleted State that is only defined in this PR,
    # but therefore, no comparison image exists so NO DIFF
    elif len(img_type) > 2:
        msg = 'No Diff could be made. There were more than one state with the same name "{0}". Please fix this.'.format(  # noqa: E501
              img_type)
        LOGGER.error(msg)
        History.log_sys_error(build_obj.pr, msg)
        return ERROR_BUILD_STATUS_CODE  # return status code = 4 (error)
    return COMPLETED_BUILD_STATUS_CODE


# Input: list of states to take screenshots of, build object
# Output: Image Object screenshots generated, Integer status code
# Edge: Can be 0 diffs generated
def generate_images(states_list, build_obj):
    img_dict = defaultdict(list)  # {'key': [<ImgObj1>, <ImgObj2>], 'key2': [...}

    for single_state in states_list:  # should run two times
        LOGGER.debug('RUN ADDD SCREENSHOT FOR ' + single_state.state_name)
        img_list = add_screenshots(single_state)

        for i in img_list:
            # key uniquely identifies a diffable screenshot
            key = "{0}{1}{2}{3}x{4}".format(i.state.state_name,
                                            i.browser_type,
                                            i.operating_system,  # {2}
                                            i.device_res_width,
                                            i.device_res_height)
            img_dict[key].append(i)
    if img_dict:
        return img_dict, None
    else:
        # There was an error in the config file or screenshot process so no image was taken
        return None, ERROR_BUILD_STATUS_CODE  # return status code for this message


# base_states_list = list of states for the BASE branch
# head_states_list = list of states for the HEAD branch
# build_id = the current (presumptuously newest build object) for the PR
# If no host, then have use a command line arguments to prompt for the BASE and HEAD host urls
#       else, have the host urls be provided by web initially then fully automate rest
def redis_entrypoint(build_id, old_build_id=None, base_host=None, head_host=None):
    build = Build.objects.get(id=build_id)
    # get a list of the states for the pr, both branches
    base_states_list = build.git_target_commit.state_set.all()
    head_states_list = build.git_source_commit.state_set.all()

    img_pairs_dict = defaultdict(lambda: defaultdict(list))
    # img_pairs_dict used to store old and new versions of base&head images
    # img_pairs_dict = {'img_key': {'BASE': [<old_img>, <new_img>], 'HEAD': [,]}, 'img_key2'}

    # enqueue the job of taking screenshots should return a img_dict prepared for diffing
    img_Q = lambda states_list: RQ_QUEUE.enqueue(generate_images, states_list, build)  # noqa: E731, E501

    LOGGER.info('Generating screenshots of states...')
    # Manual command line prompt to add the name of the HEAD branch host
    if base_host is None:
        base_host = raw_input("Provide the host for the BASE branch now: ")
    # update the urls for all BASE states to be the host domain of BASE branch
    for base_state in base_states_list:
        base_state.host_url = base_host
        base_state.full_url = base_state.get_full_url(base_host)
        base_state.save()
    # base states
    base_imgs = img_Q(base_states_list)

    # when done screenshoting, add new base images to data struct
    while not (base_imgs.result):
        time.sleep(0.1)
        # if either of these jobs fail unexpectedly, catch it with cancelled status code
        if base_imgs.is_failed is True:
            build.status_code = CANCELLED_BUILD_STATUS_CODE
            build.save()
            break
        continue

    base_imgs_dict = base_imgs.result[0]  # dict of generated image objects
    base_imgs_status_code = base_imgs.result[1]
    if base_imgs_dict:  # if its an actual img dictionary
        for b_img_key in base_imgs_dict:
            for img_obj in base_imgs_dict[b_img_key]:
                img_pairs_dict[b_img_key]['BASE'].append(img_obj)
    # IF there are any error outs while screenshotting
    elif base_imgs_dict is None and base_imgs_status_code:
        build.status_code = base_imgs_status_code
        build.save()

    # Manual command line prompt to add the name of the HEAD branch host
    if head_host is None:
        head_host = raw_input("Provide the host for the HEAD branch now: ")
    # update the urls for all HEAD states to be the host domain of HEAD branch
    for head_state in head_states_list:
        head_state.host_url = head_host
        head_state.full_url = head_state.get_full_url(head_host)
        head_state.save()
    head_imgs = img_Q(head_states_list)

    while not (head_imgs.result):
        time.sleep(0.1)
        # if either of these jobs fail unexpectedly, catch it with cancelled status code
        if head_imgs.is_failed is True:
            build.status_code = CANCELLED_BUILD_STATUS_CODE
            build.save()
            break
        continue

    head_imgs_dict = head_imgs.result[0]
    head_imgs_status_code = head_imgs.result[1]
    if head_imgs_dict:  # if its an actual img dictionary
        for h_img_key in head_imgs_dict:
            for img_obj in head_imgs_dict[h_img_key]:
                img_pairs_dict[h_img_key]['HEAD'].append(img_obj)
    # IF there are any error outs while screenshotting
    elif head_imgs_dict is None and head_imgs_status_code:
        build.status_code = head_imgs_status_code
        build.save()

    # if there is an old build, try to copy over information to this build

    '''
    USE TO TRANSFER APPROVALS FROM BUILDS BUT DIFF APPROVING IS NOT ESSENTIAL
    if old_build_id is not None:
        LOGGER.info('Transfering approvals from previous build...')
        old_build = Build.objects.get(id=old_build_id)
        transfer_old_build_data_to_new_build(img_pairs_dict, old_build)
    '''

    diff_Q = lambda img_type: RQ_QUEUE.enqueue(generate_diffs, img_type, build)  # noqa: E731
    LOGGER.info('Diffing screenshots...')

    diff_jobs = [diff_Q(img_pairs_dict[img_key]) for img_key in img_pairs_dict]
    while not all(d_job.result for d_job in diff_jobs):
        time.sleep(0.1)
        if any(d_job.is_failed is True for d_job in diff_jobs):
            build.status_code = CANCELLED_BUILD_STATUS_CODE
            build.save()
            break
        continue

    # be skeptical of perfectly running builds
    if build.status_code == IN_PROGRESS_BUILD_STATUS_CODE:
        for d in diff_jobs:
            if not build.status_code == ERROR_BUILD_STATUS_CODE and not build.status_code == d.result:  # noqa: E501
                # d.result can either be 2 or 4
                build.status_code = d.result
                build.save()

    # if there wasnt an error throughout the process then it succeeded!
    if not (build.status_code == ERROR_BUILD_STATUS_CODE or
       build.status_code == CANCELLED_BUILD_STATUS_CODE):
        History.log_initial_diffs(build)
        LOGGER.info('Completed screenshoting procedure successfully!')
    else:
        LOGGER.info('An error occured during the screenshotting procedure!')

    # convert status code to comprehensible message
    status_map = ('UNINITIATED_BUILD',
                  'IN_PROGRESS_BUILD',
                  'COMPLETED_BUILD',
                  'CANCELLED_BUILD',
                  'ERROR_BUILD')
    message = status_map[build.status_code]
    # sending message to the client
    Group("ws").send({
        "text": message,
    })


# get all the right information to start diffing
# GETS CALLED FROM: auto-screenshot.py management command
# local_dev = If True, then have use a command line arguments to prompt for the BASE and HEAD host urls  # noqa: E501
#             If False, then the have the host urls be provided by web initially then fully automate rest  # noqa: E501
def diffs_from_pr(pr_obj, base_host=None, head_host=None):
    latest_build = pr_obj.get_latest_build()
    previous_build = pr_obj.get_last_executed_build()

    latest_build.status_code = IN_PROGRESS_BUILD_STATUS_CODE  # status code 1
    latest_build.save()

    Group("ws").send({
        "text": str(latest_build.status_code),
    })

    # if new build for an existing pr, do special cases to copy relevant image data over
    if (previous_build and latest_build is not previous_build):
        RQ_QUEUE.enqueue(redis_entrypoint,
                         latest_build.id,
                         old_build_id=previous_build.id,
                         base_host=base_host,
                         head_host=head_host)
    else:  # no previous build exists
        RQ_QUEUE.enqueue(redis_entrypoint,
                         latest_build.id,
                         base_host=base_host,
                         head_host=head_host)

    # does not check if the redis_entrypoint fuction crashes to change status code to 3
    return
