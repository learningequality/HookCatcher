from django.core.management.base import BaseCommand, CommandError
from HookCatcher.management.commands.functions.add_pr_info import add_pr_info
from HookCatcher.management.commands.functions.diffs_from_pr import \
    diffs_from_pr
from HookCatcher.models import PR, Build, Commit


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
        pr_number = options['pr_number']
        new_base = options['base_commit']
        new_head = options['head_commit']

        try:
            build = Build.objects.get(pr=PR.objects.get(git_pr_number=pr_number),
                                      git_target_commit=Commit.objects.get(git_hash=new_base),
                                      git_source_commit=Commit.objects.get(git_hash=new_head))
        except PR.DoesNotExist, Commit.DoesNotExist:
            build = add_pr_info(pr_number)

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

        if build.status_code == 1:
            raise CommandError('This build is currently already in process')

        if build.status_code == 2:
            raise CommandError('This build already ran successfully previously')

        else:
            pr_obj = PR.objects.get(git_pr_number=pr_number)

            # get a list of the states for the pr, both branches
            base_states_list = build.git_target_commit.state_set.all()
            head_states_list = build.git_source_commit.state_set.all()

            # update the host domain url of base branch
            for base_state in base_states_list:
                base_state.host_url = options['base_host']
                base_state.full_url = base_state.get_full_url(options['base_host'])

                base_state.save()

            # update the host domain of head branch
            for head_state in head_states_list:
                head_state.host_url = options['head_host']
                head_state.full_url = head_state.get_full_url(options['head_host'])
                head_state.save()

            diffs_from_pr(pr_obj, base_states_list, head_states_list)
            return
