'''
GOAL: Low level command that DIFFs two images with a choice of methods
given: two images PATHS, diff them with a method of choice
return: diff image of two screenshots of a single state
'''
import os
import sh

from django.conf import settings  # database dir
# directory for storing images in the data folder
IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')


# calls image magick on two images
def imgMagickCompare(imgPath1, imgPath2, diffPath):
    diffPercent = None
    # create new folders if needed to generate this image
    if not os.path.exists(os.path.dirname(diffPath)):
        os.makedirs(os.path.dirname(diffPath))
    # the DIff image file already exists so ask to override
    elif os.path.exists(diffPath):
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


def gen_diff(diffTool, imgPath1, imgPath2, diffName):
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
    print('Generated diff')
