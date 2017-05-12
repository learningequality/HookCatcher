'''
GOAL: Low level command that generates a png image of the screenshot of a state
given: page url, config file [img resolution for screenshot, browser option]
return: png image of screenshot of the state
'''
import json
import os

import sh
from django.conf import settings  # database dir
from django.core.management.base import BaseCommand

# directory for storing images in the data folder
IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')


# retrieve the information of a single state and generate an image based on that
def genImages(url, resTuple, browser):
    # generate the specific headless browser screenshot

    # check if there is the browser is a valid option
    if (str(browser).lower() == 'phantomjs'):
        # format the name of the screenshotted image
        imgName = '{0}_{1}_{2}x{3}.png'.format(url,
                                               browser,         # {3}
                                               resTuple[0],
                                               resTuple[1])   # {5}

        # take the screenshot and save png file to a directory
        sh.phantomjs('screenshotScript/capture.js',  # where the capture.js script is
                     url,  # url for screenshot
                     '{0}/{1}'.format(IMG_DATABASE_DIR, imgName),  # img name
                     resTuple[0],  # width
                     resTuple[1])  # height

        print('Generated image: {0}/{1}'.format(IMG_DATABASE_DIR, imgName))

    else:
        print('No headless browser option named {0}'.format(browser))
    return


class Command(BaseCommand):
    help = 'Specify the Git repo, branch, and commit with the state name to take screenshots of a state'  # noqa: E501

    def add_arguments(self, parser):
        # use state UUID for identification rather thatn commitHash, repo, branch, state names
        parser.add_argument('url')
        parser.add_argument('--file', type=file)

    def handle(self, *args, **options):
        url = options['url']
        configFile = options['file']

        configList = json.load(configFile)
        print configList
        for config in configList['setting']:
            genImages(url, config['resolution'], config['browser'])

        self.stdout.write(self.style.SUCCESS('Finished'))
