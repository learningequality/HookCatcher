'''
GOAL: Takes a screenshot of a state
given: stateUUID
return: png image of screenshot of the state
 Add information about the screenshot to the Image table
'''
import os
import sh

from django.conf import settings  # database dir
from django.core.management.base import BaseCommand


# directory for storing images in the data folder
IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')


# retrieve the information of a single state and generate an image based on that
def genImages(url, resolutionsList, browsersList):
    # generate the specific headless browser screenshot
    for browser in browsersList:
        # generate the png screenshot a state per resolution

        # check if there is the browser is a valid option
        if (str(browser).lower() == 'phantomjs'):
            for resolution in resolutionsList:

                    # format the name of the screenshotted image
                    imgName = '{0}_{1}_{2}x{3}.png'.format(url,
                                                           browser,         # {3}
                                                           resolution[0],
                                                           resolution[1])   # {5}

                    # take the screenshot and save png file to a directory
                    sh.phantomjs('screenshotScript/capture.js',  # where the capture.js script is
                                 url,  # url for screenshot
                                 '{0}/{1}'.format(IMG_DATABASE_DIR, imgName),  # img name
                                 resolution[0],  # width
                                 resolution[1])  # height

                    print('Generated image: {0}/{1}'.format(IMG_DATABASE_DIR, imgName))

        else:
            print('No headless browser option named {0}'.format(browser))
    return


def getResolutions(oneRes):
    resTuple = tuple(res.strip(' ') for res in oneRes.split('x'))
    return resTuple


class Command(BaseCommand):
    help = 'Specify the Git repo, branch, and commit with the state name to take screenshots of a state'  # noqa: E501

    def add_arguments(self, parser):
        # use state UUID for identification rather thatn commitHash, repo, branch, state names
        parser.add_argument('url')
        parser.add_argument('resolutions')
        parser.add_argument('browsers')

    def handle(self, *args, **options):
        url = options['url']
        resolutionsList = [getResolutions(r) for r in options['resolutions'].split(',')]
        browsersList = [str(b).strip(' ') for b in options['browsers'].split(',')]

        self.stdout.write(self.style.SUCCESS('Generated Images...'))
        genImages(url, resolutionsList, browsersList)
        self.stdout.write(self.style.SUCCESS('Finished'))
