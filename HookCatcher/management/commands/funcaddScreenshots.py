'''
GOAL: high level generate image for the screenshot of a state and add to Image table
given: state UUID, config file [img resolution for screenshot, os, browser option]
return: png image of screenshot of a state,
        add a new image object to Image table
'''
import json
import os
import platform
import sh

from django.conf import settings  # database dir
from HookCatcher.models import Image

# directory for storing images in the data folder
IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')


def addImgData(browser, osys, imgWidth, imgHeight, stateObj):
    # generate an apporpriate namme for the
    stateAndRepo = os.path.join(stateObj.stateName, stateObj.gitRepo)
    branchAndCommit = os.path.join(stateObj.gitBranch, stateObj.gitCommit.gitHash[:7])
    imgPath = os.path.join(stateAndRepo, branchAndCommit)

    imgName = '{0}_{1}_{2}x{3}.png'.format(browser,  # {0}
                                           osys,
                                           imgWidth,  # {2}
                                           imgHeight)

    imgCompletePath = os.path.join(imgPath, imgName)
    # check if image already exists in data to prevent duplicates
    findDuplicateImg = Image.objects.filter(browserType=browser,
                                            operatingSystem=osys,
                                            width=imgWidth,
                                            height=imgHeight,
                                            state=stateObj)

    # if there was no duplicate found
    if (findDuplicateImg.count() > 0):
        findDuplicateImg = findDuplicateImg.get()
        findDuplicateImg.imgName = imgCompletePath
        return findDuplicateImg

    else:
        imgObj = Image(imgName=imgCompletePath,
                       browserType=browser,
                       operatingSystem=osys,
                       width=imgWidth,
                       height=imgHeight,
                       state=stateObj)
        imgObj.save()
        return imgObj


# retrieve the information of a single state and generate an image based on that
def genPhantom(stateObj, config):
    # generate the specific headless browser screenshot
    res = config["resolution"]
    currOS = platform.system() + ' ' + platform.release()

    i = addImgData('PhantomJs', currOS, res[0], res[1], stateObj)
    # take the screenshot and save png file to a directory
    if (i):
        sh.phantomjs('screenshotScript/capture.js',  # where the capture.js script is
                     stateObj.stateUrl,  # url for screenshot
                     '{0}/{1}'.format(IMG_DATABASE_DIR, i.imgName),  # img name
                     res[0],  # width
                     res[1])  # height

        print('Generated image: {0}/{1}'.format(IMG_DATABASE_DIR, i.imgName))
    return i


'''
I chose not to call the genScreenshot command because I need the image object to be
created first before to name the image of the screenshot in screenshot tool
'''


def addScreenshots(stateObj, configPath):
    imgList = []
    if(os.path.exists(configPath) is True):
        configFile = json.loads(open(configPath, 'r').read())
        for config in configFile:
            # check if there is the browser is a valid option
            if (str(config["id"]).lower() == 'phantom'):
                i = genPhantom(stateObj, config['config'])
                imgList.append(i)
    return imgList
