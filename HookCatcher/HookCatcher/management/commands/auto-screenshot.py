import logging

from django.core.management.base import BaseCommand, CommandError
from HookCatcher.management.commands.functions.add_pr_info import add_pr_info
from HookCatcher.management.commands.functions.diffs_from_pr import \
  diffs_from_pr
from HookCatcher.models import PR, Build, Commit

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        # the Pull Request Number to search for on git API
        parser.add_argument('pr_number', type=int)
        parser.add_argument('base_host', type=str)
        parser.add_argument('head_host', type=str)
        parser.add_argument('base_commit', type=str)
        parser.add_argument('head_commit', type=str)

    def handle(self, *args, **options):
        # ASSUME: metadata of PR, commit, build, state has already been stored in databse by webhook
        pr_obj = PR.objects.get(git_pr_number=options['pr_number'])
        new_base = Commit.objects.get(git_hash=options['base_commit'])
        new_head = Commit.objects.get(git_hash=options['head_commit'])

        try:
            build = Build.objects.get(pr=pr_obj,
                                      git_target_commit=new_base,
                                      git_source_commit=new_head)
        except Exception as e:
            LOGGER.error(e)
            build = add_pr_info(pr_obj.git_pr_number)

        '''
        USE CASE: when do we wan users to generate diffs for a particular build
        Build Status = 0 ()
            Never initiated build. A common case when new commits are added or new pr detected

        Build Status = 1
            Another Process of the same build is running

        Build Status = 2
            Build already ran before with no issues

        Build Status = 3
            If a build already exists maybe it was terminated in the middle in which case
                we want to rerun to finish off what it started
            Case if there are errors we did not program to check

        Build Status = 4
            An Error occurred last time with the process last time we ran this build
            We have an idea of what the issue was with the last build
        '''

        LOGGER.info("Initiated process for PR#{0}".format(pr_obj.git_pr_number))
        if build.status_code == 1:
            raise CommandError('This build is currently already in process')

        if build.status_code == 2:
            raise CommandError('This build already ran successfully previously')

        else:
            diffs_from_pr(pr_obj, base_host=options['base_host'], head_host=options['head_host'])
            return
