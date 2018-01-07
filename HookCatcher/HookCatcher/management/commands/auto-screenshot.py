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

        # for some reason the pr number was not recorded previously from a webhook
        if PR.objects.filter(git_pr_number=pr_number).count() < 1:
            # check if the build with these commits on this PR already exists
            add_pr_info(pr_number)
        else:
            find_build = Build.objects.filter(pr=PR.objects.get(git_pr_number=pr_number),
                                              git_target_commit=Commit.objects.get(git_hash=new_base),  # noqa: E501
                                              git_source_commit=Commit.objects.get(git_hash=new_head))  # noqa: E501
            # this is a new build
            if find_build.count() < 1:
                # runs most recent commits EVEN IF =/= head_commit & base_commit
                add_pr_info(pr_number)  # retrieves metadata for latest build of this PR

        # get the newest build we are generating for
        pr_obj = PR.objects.get(git_pr_number=pr_number)
        latest_build = pr_obj.get_latest_build()

        if latest_build:
            # get a list of the states for the pr, both branches
            base_states_list = latest_build.git_target_commit.state_set.all()
            head_states_list = latest_build.git_source_commit.state_set.all()

            # update the host domain url of base branch
            for base_state in base_states_list:
                base_state.host_url = options['base_host']
                base_state.save()

            # update the host domain of head branch
            for head_state in head_states_list:
                head_state.host_url = options['head_host']
                head_state.save()

            diffs_from_pr(pr_obj, base_states_list, head_states_list)
        else:
            raise CommandError('No Builds for PR {0}'.format(pr_number))
