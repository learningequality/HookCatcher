'''
GOAL: Low level command that DIFFs two images with a choice of methods
given: two images PATHS, diff them with a method of choice
return: diff image of two screenshots of a single state
'''
from django.core.management.base import BaseCommand
from funcgenDiff import genDiff


class Command(BaseCommand):
    help = 'Choose two image screenshots of the same state, resolution, os, and browser to take a diff of'  # noqa: E501

    def add_arguments(self, parser):
        # use state UUID for identification rather thatn commitHash, repo, branch, state names
        parser.add_argument('diffTool')
        parser.add_argument('imgPath1')
        parser.add_argument('imgPath2')
        parser.add_argument('diffName')

    def handle(self, *args, **options):
        # call genDiff function
        genDiff(options['diffTool'],
                options['imgPath1'],
                options['imgPath2'],
                options['diffName'])
