'''
GOAL: Low level command that generates a png image of the screenshot of a state
given: page url, config file [img resolution for screenshot, browser option]
return: png image of screenshot of the state
'''
import json
import os
import platform

import sh
from django.conf import settings  # database dir
from django.core.management.base import BaseCommand, CommandError

# directory for storing images in the data folder
IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')


# retrieve the information of a single state and generate an image based on that
def genPhantom(url, imgName, config):
    # generate the specific headless browser screenshot

    res = config["resolution"]
    currOS = platform.system() + ' ' + platform.release()  # get current os

    # add info about the metadata of the screenshot itself in the iamge name.
    # Use splittext to take out the extension.
    imgName = '{0}_PhantomJS_{1}_{2}_{3}.png'.format(os.path.splitext(imgName)[0],
                                                     currOS,
                                                     res[0],
                                                     res[1])

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
        parser.add_argument('imgName')

    def handle(self, *args, **options):
        try:
            url = options['url']
            imgName = options['imgName']
            configPath = settings.SCREENSHOT_CONFIG

            if(os.path.exists(configPath) is True):
                configFile = json.loads(open(configPath, 'r').read())
                print('Generating image(s)...')
                for config in configFile:
                    # check if there is the browser is a valid option
                    if (str(config["id"]).lower() == 'phantom'):
                        genPhantom(url, imgName, config['config'])
            else:
                raise CommandError("The screenshot config file defined in 'user_settings.py' doesn't exist!")  # noqa: E501
        except:
                raise CommandError('Please provide all args for command: genScreenshot <Url> <Image Name>')  # noqa: E501
        self.stdout.write(self.style.SUCCESS('Finished'))
