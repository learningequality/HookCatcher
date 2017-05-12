'''
GOAL: Low level command that DIFFs two images with a choice of methods
given: two images PATHS, diff them with a method of choice
return: diff image of two screenshots of a single state
'''
import os
import sh

from django.conf import settings  # database dir
from django.core.management.base import BaseCommand

# directory for storing images in the data folder
IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')


# calls image magick on two images
def imgMagickCompare(imgPath1, imgPath2):
    # intialize a temp variable to save the path names
    imgPath1temp = imgPath1
    imgPath2temp = imgPath2

    # parse out the parts of the image name related to directory paths for diff name
    # that way there are no '/' characters that mess up the directory of the diff image
    indx1 = imgPath1temp.find(IMG_DATABASE_DIR) + 1
    indx2 = imgPath2temp.find(IMG_DATABASE_DIR) + 1
    if (indx1 != -1):
        imgPath1temp = imgPath1temp[(indx1 + len(IMG_DATABASE_DIR)):]
        print(imgPath1temp)

    if (indx2 != -1):
        imgPath2temp = imgPath2temp[(indx2 + len(IMG_DATABASE_DIR)):]
        print(imgPath2temp)

    # name of the diff that concatenates the truncated version of both image names
    imgDiffName = ('imgDIFF_{0}_{1}').format(imgPath1temp, imgPath2temp)
    imgDiffName = os.path.join(IMG_DATABASE_DIR, imgDiffName)
    try:
        # Diff screenshot name using whole path to reference images
        sh.compare('-metric', 'PSNR', imgPath1, imgPath2, imgDiffName)
    except sh.ErrorReturnCode_1, e:
        diffPercent = float(e.stderr)
        print diffPercent
    return


class Command(BaseCommand):
    help = 'Choose two image screenshots of the same state, resolution, os, and browser to take a diff of'  # noqa: E501

    def add_arguments(self, parser):
        # use state UUID for identification rather thatn commitHash, repo, branch, state names
        parser.add_argument('diffTool')
        parser.add_argument('imgPath1')
        parser.add_argument('imgPath2')

    def handle(self, *args, **options):
        # Make sure these images exist in the image database
        diffTool = options['diffTool']
        imgPath1 = options['imgPath1']
        imgPath2 = options['imgPath2']

        if(str(diffTool).lower() == 'imagemagick'):
            self.stdout.write(self.style.SUCCESS('Generating Diff...'))
            imgMagickCompare(imgPath1, imgPath2)
        else:
            print('{0} is not an image diffing option'.format(diffTool))

        self.stdout.write(self.style.SUCCESS('Generated diff'))
