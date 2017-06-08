'''
GOAL: Low level command that DIFFs two images with a choice of methods
given: two images PATHS, diff them with a method of choice
return: diff image of two screenshots of a single state
'''
import os
import sh

from django.conf import settings  # database dir
from django.core.management.base import BaseCommand, CommandError
# directory for storing images in the data folder
IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')


# calls image magick on two images
def imgMagickCompare(imgPath1, imgPath2, diffPath):
    diffPercent = 0.00
    try:

        if not os.path.exists(os.path.dirname(diffPath)):
            os.makedirs(os.path.dirname(diffPath))

        # Diff screenshot name using whole path to reference images
        sh.compare('-metric', 'RMSE', imgPath1, imgPath2, diffPath)

    except sh.ErrorReturnCode_1, e:
        diffOutput = e.stderr

        # returns pixels and a % in () we only want the % ex: 25662.8 (0.39159)
        idxPercent = diffOutput.index('(') + 1
        diffPercent = diffOutput[idxPercent:len(diffOutput)-1]
        print "Percent difference: " + diffPercent
    return diffPercent


class Command(BaseCommand):
    help = 'Choose two image screenshots of the same state, resolution, os, and browser to take a diff of'  # noqa: E501

    def add_arguments(self, parser):
        # use state UUID for identification rather thatn commitHash, repo, branch, state names
        parser.add_argument('diffTool')
        parser.add_argument('imgPath1')
        parser.add_argument('imgPath2')
        parser.add_argument('diffName')

    def handle(self, *args, **options):
        # Make sure these images exist in the image database
        diffTool = options['diffTool']
        imgPath1 = options['imgPath1']
        imgPath2 = options['imgPath2']
        diffName = options['diffName']

        if(os.path.exists(imgPath1) is True):
            if(os.path.exists(imgPath2) is True):

                if(str(diffTool).lower() == 'imagemagick'):
                    print('Generating Diff...')
                    diffPercent = imgMagickCompare(imgPath1, imgPath2, diffName)

                    return diffPercent

                else:
                    raise CommandError('{0} is not an image diffing option'.format(diffTool))
            else:
                raise CommandError('The second image to be compared does not exist')
        else:
            raise CommandError('The first image to be compared does not exist')
        self.stdout.write(self.style.SUCCESS('Generated diff'))
