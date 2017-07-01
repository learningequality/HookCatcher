from django.core.management.base import BaseCommand
from HookCatcher.management.commands.functions.diffs_from_pr import \
  diffs_from_pr


class Command(BaseCommand):

    def add_arguments(self, parser):
        # the Pull Request Number to search for on git API
        parser.add_argument('prNumber', type=int)

    def handle(self, *args, **options):
        diffs_from_pr(options['prNumber'])
