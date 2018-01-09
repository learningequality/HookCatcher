'''
GOAL: high level generate image for the screenshot of a state and add to Image table
given: state UUID, config file [img resolution for screenshot, os, browser option]
return: png image of screenshot of a state,
        add a new image object to Image table
'''
from django.core.management.base import BaseCommand, CommandError
from HookCatcher.management.commands.functions.add_screenshots import \
  add_screenshots
from HookCatcher.models import State


class Command(BaseCommand):

    def add_arguments(self, parser):
        # use state UUID for identification rather thatn commitHash, repo, branch, state names
        parser.add_argument('stateUUID')

    '''
    I chose not to call the genScreenshot command because I need the image object to be
    created first before to name the image of the screenshot in screenshot tool
    '''

    def handle(self, *args, **options):
        try:
            s = State.objects.get(state_uuid=options['stateUUID'])
        except State.DoesNotExist:
            raise CommandError('State "%s" does not exist' % options['stateUUID'])
        add_screenshots(s)
