import os
import sh

from django.conf import settings  # database dir
from django.core.management.base import BaseCommand, CommandError
from HookCatcher.models import Commit, Image, State


# directory for storing images in the data folder
IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')


# retrieve the information of a single state and generate an image based on that
def genImages(stateObj):

    numGenerated = 0
    IMG_RESOLUTIONS = [(300, 400), (600, 800), (1200, 1800)]
    BROWSER_TYPE = 'PhantomJs'
    OS = 'MAC OS Sierra'

    # generate the png screenshot a state per reesolution
    for resolution in IMG_RESOLUTIONS:
        # format the name of the screenshotted image
        imgName = '{0}_{1}_{2}x{3}.png'.format(stateObj.stateUUID,
                                               BROWSER_TYPE,  # {3}
                                               resolution[0],
                                               resolution[1])   # {5}
        # indempotent check if this image is already generated don't do again
        if (Image.objects.filter(imgName=imgName).count() < 1):
            # take the screenshot and save png file to a directory
            sh.phantomjs('screenshotScript/capture.js',  # where the capture.js script is
                         stateObj.stateUrl,  # url for screenshot
                         '{0}/{1}'.format(IMG_DATABASE_DIR, imgName),  # img name
                         resolution[0],  # width
                         resolution[1])  # height

            print('Generated image: {0}/{1}'.format(IMG_DATABASE_DIR, imgName))
            numGenerated += 1

            i = Image(imgName=imgName,
                      browserType=BROWSER_TYPE,
                      operatingSystem=OS,
                      width=resolution[0],
                      height=resolution[1],
                      state=stateObj)
            i.save()
        else:
            print('Already had been generated: {0}'.format(imgName))
    return numGenerated


class Command(BaseCommand):
    help = 'Specify the Git repo, branch, and commit with the state name to take screenshots of a state'  # noqa: E501

    def add_arguments(self, parser):
        # use state UUID for identification rather thatn commitHash, repo, branch, state names
        parser.add_argument('stateUUID')

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Generating Images...'))
            s = State.objects.get(stateUUID=options['stateUUID'])

            numGenerated = genImages(s)
        except Commit.DoesNotExist:
            raise CommandError('Commit "%s" does not exist' % options['commitHash'])

        self.stdout.write(self.style.SUCCESS('Generated %d images' % numGenerated))
