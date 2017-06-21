from django.core.management.base import BaseCommand
from funcaddState import addState


class Command(BaseCommand):
    help = 'Add a state into the states table'

    def add_arguments(self, parser):
        # need to open the JSON file from the path
        parser.add_argument('pathToJSONfile')
        parser.add_argument('gitRepo')
        parser.add_argument('gitBranch')
        parser.add_argument('gitCommitHash')

    def handle(self, *args, **options):
        addState(options['pathToJSONfile'],
                 options['gitRepo'],
                 options['gitBranch'],
                 options['gitCommitHash'])
