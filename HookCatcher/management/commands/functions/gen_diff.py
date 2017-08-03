'''
GOAL: Low level command that DIFFs two images with a choice of methods
given: two images PATHS, diff them with a method of choice
return: diff image of two screenshots of a single state
'''
import os
import tempfile

import requests
import sh
from django.conf import settings  # database dir
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.core.validators import URLValidator
from HookCatcher.models import Diff, Image

# directory for storing images in the data folder
IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')


# Helper function for creating the image path and then return if that file exists
def img_exists(img_file_name):
    # check if the file name is url or nah and see if that url is real
    validator = URLValidator()
    try:
        validator(img_file_name)
        return requests.get(img_file_name).status_code == 200
    except ValidationError:
        return os.path.exists(os.path.join(settings.MEDIA_ROOT, img_file_name))


def is_url(img_file_name):
    validator = URLValidator()
    try:
        validator(img_file_name)
        return True
    except ValidationError:
        return False


# generates the appropriate name for the new diff image
def getDiffImageName(img1, img2):
    # format the name of the diff image to be base(target) commit -> diffs -> head(source) commit
    # formula: (baseGitinfo)/diffs/(headGitInfo)/(imgMetadata).png

    state_repo_base = os.path.join(img1.state.state_name, img1.state.git_commit.git_repo)
    branch_commit_base = os.path.join(img1.state.git_commit.git_branch,
                                      img1.state.git_commit.git_hash[:7])
    img_path_base = os.path.join(state_repo_base, branch_commit_base)

    state_repo_head = os.path.join(img2.state.state_name, img2.state.git_commit.git_repo)
    branch_commit_head = os.path.join(img2.state.git_commit.git_branch,
                                      img2.state.git_commit.git_hash[:7])
    img_path_head = os.path.join(state_repo_head, branch_commit_head)

    diff_path = os.path.join(os.path.join(img_path_base, 'diffs'), img_path_head)
    diff_name = '{0}_{1}_{2}x{3}.png'.format(img1.browser_type,  # {0}
                                             img1.operating_system,
                                             img1.device_res_width,    # {2}
                                             img1.device_res_height)
    diff_complete_path = os.path.join(diff_path, diff_name)
    return diff_complete_path


# calls image magick on two images
# saves the picture first into a temporary iamge and then
def imagemagick(img1_path, img2_path, diff_name, diff_obj):
    diff_percent = None

    with tempfile.NamedTemporaryFile(suffix='.png') as temp_diff:
        try:
            # Diff screenshot name using whole path to reference images
            sh.compare('-metric', 'RMSE', img1_path, img2_path, temp_diff.name)
        # imagemagick outputs the diff percentage in std.err, will run exception everytime
        except sh.ErrorReturnCode_1, e:
            diffOutput = e.stderr

            # returns pixels and a % in () we only want the % ex: 25662.8 (0.39159)
            idxPercent = diffOutput.index('(') + 1
            diff_percent = diffOutput[idxPercent:len(diffOutput) - 1]

        finally:
            if diff_percent:
                diff_obj.diff_percent = diff_percent
            diff_obj.diff_img_file.save(diff_name, temp_diff, save=True)
            print('Finished adding new Diff named: "{0}"'.format(os.path.join(settings.MEDIA_ROOT,
                                                                              diff_obj.diff_img_file.name)))  # noqa: E501
    return diff_percent


# responsible for checking if the images exist and generating the diff if th ydo
def validate_diff(diff_tool, img1, img2):
    # get the full path of the image if the image needed is in local storage else keep url
    if is_url(img1.img_file.name):
        img1_path = os.path.join(settings.MEDIA_ROOT, img1.img_file.name)
    else:
        img1_path = img1.img_file.name
    if is_url(img2.img_file.name):
        img2_path = os.path.join(settings.MEDIA_ROOT, img2.img_file.name)
    else:
        img2_path = img2.img_file.name

    if img_exists(img1.img_file.name) is True:
        if img_exists(img2.img_file.name) is True:
            # generate the name of the new Diff image
            diff_name = getDiffImageName(img1, img2)

            try:
                # check if image already exists in data to prevent duplicates
                duplicate_diff = Diff.objects.get(target_img=img1,
                                                  source_img=img2)
                # see if the actual diff image exists, else create one
                if (duplicate_diff.diff_img_file.name == '' or
                    not os.path.exists(os.path.join(settings.MEDIA_ROOT,
                                                    duplicate_diff.diff_img_file.name))):
                    if diff_tool == 'imagemagick':
                        # generate new diff, but make sure only one entry of the image is in model
                        imagemagick(img1_path, img2_path, diff_name, duplicate_diff)
                        return
                    else:
                        print('{0} is not an image diffing option'.format(diff_tool))
                else:
                    print('Perceptual diff "{0}" already exists'.format(duplicate_diff.diff_img_file.name))  # noqa: E501
            except Diff.DoesNotExist:
                # if there is no duplicate in the database, make one in db and generate diff
                placeholer_diff = Diff(diff_img_file=None,
                                       target_img=img1,
                                       source_img=img2)
                if diff_tool == 'imagemagick':
                    imagemagick(img1_path, img2_path, diff_name, placeholer_diff)
            # if the diff is or isn't created return nothing
            return
        else:
            print('The second image: "{0}" to be compared does not exist'.format(img2_path))
    else:
        print ('The first image: "{0}"  to be compared does not exist'.format(img1_path))


# most outfacing command that adds diff to the database models and generates the diff
def gen_diff(img_name1, img_name2, diff_tool='imagemagick'):
    try:
        # Make sure these images exist in the image database
        img1 = Image.objects.get(img_file=img_name1)  # target screenshot
        img2 = Image.objects.get(img_file=img_name2)  # source screenshot
    except Image.DoesNotExist:
        raise CommandError('At least one of the two images does not exist in the database')

    # if there is a valid diff method picked
    if str(diff_tool).lower() == 'imagemagick':
        validate_diff(str(diff_tool).lower(), img1, img2)
    else:
        print('{0} is not an image diffing option'.format(diff_tool))
    return
