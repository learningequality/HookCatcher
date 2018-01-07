'''
        Desired output ->
        1. Relevant git Commits and PR information is added to our tables
        2. images are taken for all new states BUT NOT FOR PREXISTING STATES THAT HAVE IMAGES
        3. Diffs are generated for all pairs of images that can be diffed

        ~ If no states are even checked in, do nothing.
        ~ if PR number isn''t valid, do nothing
'''
import time
from collections import defaultdict

import django_rq
from add_screenshots import add_screenshots
from HookCatcher.management.commands.functions.gen_diff import gen_diff
from HookCatcher.management.commands.functions.new_commit_old_pr import \
  new_commit_old_pr
from HookCatcher.models import Build, Diff, History

RQ_QUEUE = django_rq.get_queue('default')


def is_int(var):
    try:
        int(var)
    except TypeError:  # not an int
        return False
    return True


def generate_diffs(img_dict, build_obj):
    for img_pair in img_dict:
        # the list associated to a key should be exactly 2 one for head one for branch
        # else it is invalid for generating a diff
        if len(img_dict[img_pair]) == 2:
            if (not img_dict[img_pair][0].image_rendered() or
               not img_dict[img_pair][1].image_rendered()):
                temp_diff = Diff(target_img=img_dict[img_pair][0], source_img=img_dict[img_pair][1])
                temp_diff.save()
            else:
                gen_diff(img_dict[img_pair][0].img_file.name,
                         img_dict[img_pair][1].img_file.name)

        elif len(img_dict[img_pair]) == 1:
            # rather common use case when editting list of states so not an error
            msg = 'There is a new or deleted State named: "{0}" that is only defined in Branch "{1}"'.format(  # noqa: E501
                  img_dict[img_pair][0].state.state_name,
                  img_dict[img_pair][0].state.git_commit.git_branch)
            print msg
        else:
            msg = 'No Diff could be made. There were more than one state with the same name "{0}" in Branch "{1}". Please fix this.'.format(  # noqa: E501
                  img_dict[img_pair][0].state.state_name,
                  img_dict[img_pair][0].state.git_commit.git_branch)
            print msg
            History.log_sys_error(build_obj.pr, msg)
            return 4  # return status code = 4 (error)

    # Log all the types of diffs that have been saved
    # TODO: CANT CALL Log initial diffs from here
    # History.log_initial_diffs(build_obj.pr)
    return 2


# parrallel processes for each stateName from here
    # input: A single stateName
    # Output: Screenshots for all states, All diffs possible
    # Edge: Can be 0 diffs generated
def generate_images(state_name, build_obj):
    img_dict = defaultdict(list)  # {'key': [<ImgObj1>, <ImgObj2>], 'key2': [...}

    for single_state in state_name:  # should run two times
        print 'RUN ADDD SCREENSHOT FOR ' + single_state.state_name
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
        return img_dict
    else:
        msg = 'There was an error in the config file or screenshot process so no image was taken'  # noqa: E501
        print msg
        History.log_sys_error(build_obj.pr, msg)
        return 4  # return status code for this message


def redis_entrypoint(new_states_dict, build_id):
    build = Build.objects.get(id=build_id)

    # enqueue the job of taking screenshots should return a img_dict prepared for diffing
    img_Q = lambda state_name: RQ_QUEUE.enqueue(generate_images, new_states_dict[state_name], build)  # noqa: E731, E501
    print('Generating screenshots of states...')

    image_jobs = [img_Q(state_name) for state_name in new_states_dict]
    list_image_dict = []

    while not all(i_job.result for i_job in image_jobs):
        time.sleep(0.1)
        continue

    # Add image_dicts in to a list
    for i in image_jobs:
        if i.result and not is_int(i.result):  # if its an actual img dictionary
            list_image_dict.append(i.result)
        elif is_int(i.result):
            build.status_code = i.result
            build.save()

    diff_Q = lambda img_dict: RQ_QUEUE.enqueue(generate_diffs, img_dict, build)  # noqa: E731
    print('Diffing screenshots...')

    diff_jobs = [diff_Q(img_dict) for img_dict in list_image_dict]
    while not all(d_job.result for d_job in diff_jobs):
        time.sleep(0.1)
        continue

    for d in diff_jobs:
        if not build.status_code == d.result:
            build.status_code = d.result
            build.save()

    # TODO NEED TO CHANGE STATUS CODE HANDLING TO NOT PASS BUILD OBJ
    # if there wasnt an error throughout the process then it succeeded!
    if not (build.status_code == 4 or build.status_code == 3):
        build.status_code = 2  # status code 2 = build Completed!
        build.save()
        print('Completed screenshoting procedure successfully!')
    print('Error occured with the screenshoting procedure!')


# get all the right information to start diffing
# GETS CALLED FROM: auto-screenshot.py management command
def diffs_from_pr(pr_obj, base_states_list, head_states_list):
    latest_build = pr_obj.get_latest_build()
    previous_build = pr_obj.get_last_executed_build()

    # if new build for old pr
    if latest_build.status_code == 0:
        # prev.status = 0 means
        if (previous_build and
           previous_build.status_code != 0 and latest_build is not previous_build):
            latest_build.status_code = 1  # status code 1 = build in progress
            latest_build.save()
            new_commit_old_pr(previous_build, base_states_list, head_states_list)

        # if new build for new pr
        else:
            latest_build.status_code = 1  # status code 1 = build in progress
            latest_build.save()
            # dictionary of states that were added {'stateName1': (baseVers, headVers), ...}
            new_states_dict = defaultdict(list)
            # NOTE: if people name the state wrong this can cause errors in the system
            for base_state in base_states_list:
                new_states_dict[base_state.state_name].append(base_state)
            for head_state in head_states_list:
                # {'key' : baseStateObj, headStateObj, 'key': ...}
                new_states_dict[head_state.state_name].append(head_state)

            RQ_QUEUE.enqueue(redis_entrypoint, new_states_dict, latest_build.id)

    return
