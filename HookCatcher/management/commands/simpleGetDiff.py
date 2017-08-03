'''
GOAL: Low level command that DIFFs two images with a choice of methods
given: two images PATHS, diff them with a method of choice
return: diff image of two screenshots of a single state
'''
import os
import sh

from django.conf import settings  # database dir
from django.core.management.base import BaseCommand
from HookCatcher.management.commands.functions.gen_diff import gen_diff


# directory for storing images in the data folder
IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')


# calls image magick on two images
def imgMagickCompare(imgPath1, imgPath2, diffPath):
    diffPercent = None
    # create new folders if needed to generate this image
    if os.path.dirname(diffPath) is not '' and not os.path.exists(os.path.dirname(diffPath)):
        os.makedirs(os.path.dirname(diffPath))
    # the DIff image file already exists so ask to override
    if os.path.exists(diffPath):
        print('Diff image "{0}" already exists.'.format(diffPath))
        user_input = raw_input("Overwrite the image? (y/n): ")
        if(user_input == 'y'):
            print('Overwriting...')
        else:
            # the user did not want to override the image
            # don't run Imagemagick and don't update database
            return None
    try:
        # Diff screenshot name using whole path to reference images
        sh.compare('-metric', 'RMSE', imgPath1, imgPath2, diffPath)
    except sh.ErrorReturnCode_1, e:
        diffOutput = e.stderr

        # returns pixels and a % in () we only want the % ex: 25662.8 (0.39159)
        idxPercent = diffOutput.index('(') + 1
        diffPercent = diffOutput[idxPercent:len(diffOutput)-1]
        print "Percent difference: " + diffPercent
        pass
    return diffPercent


def gen_diff(imgPath1, imgPath2, diffTool='imagemagick', diffName):
    if(os.path.exists(imgPath1) is True):
        if(os.path.exists(imgPath2) is True):

            if(str(diffTool).lower() == 'imagemagick'):
                diffPercent = imgMagickCompare(imgPath1, imgPath2, diffName)
                return diffPercent
            else:
                print('{0} is not an image diffing option'.format(diffTool))
        else:
            print('The second image: "{0}" to be compared does not exist'.format(imgPath2))
    else:
        print ('The first image: "{0}"  to be compared does not exist'.format(imgPath1))
    return

class Command(BaseCommand):
    help = 'Choose two image screenshots of the same state, resolution, os, and browser to take a diff of'  # noqa: E501

    def add_arguments(self, parser):
        # use state UUID for identification rather thatn commitHash, repo, branch, state names
        parser.add_argument('diffTool')
        parser.add_argument('imgPath1')
        parser.add_argument('imgPath2')
        parser.add_argument('diffName')

    def handle(self, *args, **options):
        # call genDiff function
        print options['diffName']
        diff_percent = gen_diff(options['imgPath1'],
                                options['imgPath2'],
                                options['diffTool'],
                                options['diffName'])
        if diff_percent:
            print('Diff: "{0}" is {1} different'.format(options['diffName'], diff_percent))