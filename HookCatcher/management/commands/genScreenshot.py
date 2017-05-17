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
def genPhantom(url, config):
    # generate the specific headless browser screenshot

    res = config["resolution"]
    # format the name of the screenshotted image
    imgName = '{0}_{1}_{2}x{3}.png'.format(url,
                                           'Phantom',         # {3}
                                           res[0],
                                           res[1])   # {5}

    # take the screenshot and save png file to a directory
    sh.phantomjs('screenshotScript/capture.js',  # where the capture.js script is
                 url,  # url for screenshot
                 '{0}/{1}'.format(IMG_DATABASE_DIR, imgName),  # img name
                 res[0],  # width
                 res[1])  # height

    print('Generated image: {0}/{1}'.format(IMG_DATABASE_DIR, imgName))

    return


class Command(BaseCommand):
    help = 'Specify the Git repo, branch, and commit with the state name to take screenshots of a state'  # noqa: E501

    def add_arguments(self, parser):
        # use state UUID for identification rather thatn commitHash, repo, branch, state names
        parser.add_argument('url')
        parser.add_argument('configPath')

    def handle(self, *args, **options):
        url = options['url']
        configPath = options['configPath']

        if(os.path.exists(configPath) is True):
            configFile = json.loads(open(configPath, 'r').read())
            for config in configFile:
                # check if there is the browser is a valid option
                if (str(config["id"]).lower() == 'phantom'):
                    genPhantom(url, config['config'])

        self.stdout.write(self.style.SUCCESS('Finished'))
