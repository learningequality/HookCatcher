from __future__ import unicode_literals

import uuid

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator  # IntegerField Range
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q  # filter Build for status_code OR status_code
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    git_client_id = models.CharField(max_length=100)
    git_client_secret = models.CharField(max_length=100)
    git_access_token = models.CharField(max_length=100)

    def __str__(self):
        return '%s' % (self.user.username)


# Create your models here.
@python_2_unicode_compatible
class Commit(models.Model):
    git_repo = models.CharField(max_length=200)
    git_branch = models.CharField(max_length=200)
    git_hash = models.CharField(unique=True, max_length=200)

    # function to retrieve a list of images that pertain to this PR
    def get_images(self):
        image_list = []  # list of image objects pertain to this commit
        states = self.state_set.all()
        for state in states:
            image_list.extend(state.image_set.all())
        return image_list

    def __str__(self):
        return '%s/%s %s' % (self.git_repo, self.git_branch, self.git_hash)


# Fields that make a state unique: stateName, gitRepo, gitBranch, gitCommit
@python_2_unicode_compatible
class State(models.Model):
    state_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    state_name = models.CharField(max_length=200)
    state_desc = models.TextField()
    state_url = models.TextField()
    git_commit = models.ForeignKey(Commit, on_delete=models.CASCADE)  # many commits for one state
    host_url = models.TextField(null=True, blank=True)
    login_username = models.CharField(max_length=200, null=True, blank=True)
    login_password = models.CharField(max_length=200, null=True, blank=True)
    full_url = models.TextField(null=True, blank=True)

    def get_full_url(self, host_url):
        if host_url:
            # want in the form: 'host.com' + '/state_url'
            if host_url[-1:] == '/':
                host_url = host_url[:-1]
            if not self.state_url[0] == '/':
                self.state_url = '/' + self.state_url
            return host_url + self.state_url
        else:
            return self.state_url

    def __str__(self):
        return '%s, %s:%s %s' % (self.state_name,
                                 self.git_commit.git_repo,
                                 self.git_commit.git_branch,
                                 self.git_commit.git_hash[:7])


@python_2_unicode_compatible
class PR(models.Model):
    git_repo = models.CharField(max_length=200)
    git_title = models.TextField()
    git_pr_number = models.IntegerField(unique=True)

    # when a new commit is added to the PR but nothing done with that commit yet
    def get_latest_build(self):
        all_builds = self.build_set.all().order_by('-date_time', '-pr_version')
        return all_builds.first()

    # use this method thiso display the last processed build information of a PR
    def get_last_executed_build(self):
        all_builds = self.build_set.all().filter(~Q(status_code=0)).order_by('-date_time', '-pr_version')  # noqa: E501
        if len(all_builds) > 0:
            return all_builds.first()
        else:
            return None

    def __str__(self):
        return '%s: PR #%d' % (self.git_repo, self.git_pr_number)


@python_2_unicode_compatible
class Build(models.Model):
    pr = models.ForeignKey(PR, on_delete=models.CASCADE)
    pr_version = models.IntegerField()
    date_time = models.DateTimeField()
    # BASE brach of the git pull request, commonly release branch
    # call state.gitCommit.targetCommit_set.all() to get PR's where state is used as a target
    git_target_commit = models.ForeignKey(Commit, related_name='target_commit_in_PR',
                                          on_delete=models.CASCADE)
    # HEAD brach of the git pull request, commonly personal branch
    git_source_commit = models.ForeignKey(Commit, related_name='source_commit_in_PR',
                                          on_delete=models.CASCADE)
    # status code meanings
    # 0: Build not initiated
    # 1: Build in progress
    # 2: Build completed
    # 3: Build cancelled
    # 4: Build Error
    status_code = models.IntegerField(default=0,
                                      validators=[MaxValueValidator(4), MinValueValidator(0)])

    # function to retrieve a list of diffs that pertain to this PR
    def get_diffs(self):
        target_diff_list = []  # final list of diff objects that pertain to this pr
        source_diff_list = []
        # get 2 lists of images for target and source commit
        # find the common diffs from the diffs linked to those images
        for target_image in self.git_target_commit.get_images():
            target_diff_list.extend(target_image.target_img_in_Diff.all())

        for source_image in self.git_source_commit.get_images():
            source_diff_list.extend(source_image.source_img_in_Diff.all())

        # find the intersection between the two lists in case image is used in mulitple diffs
        return set(target_diff_list) & set(source_diff_list)

    def get_new_states_images(self):
        new_states = []  # list of images that pertain to newly tracked states for this PR Build
        for image in self.git_source_commit.get_images():
            is_new_state = True
        # a new commit old pr creates a new iamge object for all the new screenshots
        # no new diffs are bieng made for new images
        # the new image objects have new files attached to them

            if len(image.source_img_in_Diff.all()) > 0:
                # find a diff with matching source and target git_commits in the PR Build
                for diff in image.source_img_in_Diff.all():
                    # if the diff has a target and source of the pr then it isn't new
                    if diff.target_img.state.git_commit == self.git_target_commit:
                        is_new_state = False
            if is_new_state:
                new_states.append(image)
        return new_states

    def get_deleted_states_images(self):
        deleted_states = []
        for image in self.git_target_commit.get_images():
            is_deleted_state = True
            if len(image.target_img_in_Diff.all()) > 0:
                # find a diff with matching source and target git_commits with the pr_obj
                for diff in image.target_img_in_Diff.all():
                    # if the diff has a target and source of the pr then it isn't new
                    if diff.source_img.state.git_commit == self.git_source_commit:
                        is_deleted_state = False
            if is_deleted_state:
                deleted_states.append(image)
        return deleted_states

    def __str__(self):
        return 'PR #{1} v{2}: status {0}'.format(self.status_code,
                                                 self.pr.git_pr_number,
                                                 self.pr_version)


@python_2_unicode_compatible
class History(models.Model):
    time = models.DateTimeField(auto_now=True)
    message = models.TextField()
    is_error = models.BooleanField(default=False)
    pr = models.ForeignKey(PR, on_delete=models.CASCADE)

    # record actions in a Pull Request Event Payload to History
    @classmethod
    def log_pr_action(cls, pr_number, git_payload_action, username):
        msg = 'PR #{0} has been {1} by {2}'.format(pr_number,
                                                   git_payload_action,
                                                   username)
        pr_obj = PR.objects.get(git_pr_number=pr_number)
        cls(message=msg, pr=pr_obj).save()
        return

    # record how many diffs were generated and how many still avaliable in history
    @classmethod
    def log_initial_diffs(cls, build_obj):
        target_imgs = len(build_obj.git_target_commit.get_images())
        source_imgs = len(build_obj.git_source_commit.get_images())
        total_num_imgs = target_imgs + source_imgs
        if total_num_imgs > 0:
            msg = '{0} screenshots were generated'.format(total_num_imgs)
            cls(message=msg, pr=build_obj.pr).save()
        return

    # record in history when a user manually approves of a diff (probably too granular)
    @classmethod
    def log_user_approval(cls, pr_obj, diff_obj, username):
        msg = 'Diff of state "{0}" was approved by "{1}"'.format(
              diff_obj.target_img.state.state_name, username)
        cls(message=msg, pr=pr_obj).save()
        return

    # record in history any internal system errors
    @classmethod
    def log_sys_error(cls, pr_obj, error_message):
        cls(message=error_message, pr=pr_obj, is_error=True).save()
        return

    def __str__(self):
        return 'PR #%d: %s' % (self.pr.git_pr_number, self.message)


@python_2_unicode_compatible
class Image(models.Model):
    img_file = models.ImageField(upload_to='img', max_length=2000, null=True, blank=True)
    browser_type = models.CharField(max_length=200)
    operating_system = models.CharField(max_length=200)
    device_res_width = models.IntegerField()
    device_res_height = models.IntegerField()
    is_approved = models.BooleanField(default=False)

    # many Images to one State (for multiple browsers)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    # Returns the full path of the image_file or the url depending on where it stored
    def get_location(self):
        try:
            return self.img_file.url
        except NotImplementedError:
            pass
        try:
            return self.img_file.path
        except NotImplementedError:
            pass
        return None

    def __str__(self):
        return self.img_file.name


@python_2_unicode_compatible
class Diff(models.Model):
    diff_img_file = models.ImageField(upload_to='img', max_length=2000, null=True, blank=True)
    # GITHUB BASE of a PR (before state), many Diffs to one Image
    target_img = models.ForeignKey(Image, related_name='target_img_in_Diff',
                                   on_delete=models.CASCADE)
    # GITHUB HEAD of a PR (after state)
    source_img = models.ForeignKey(Image, related_name='source_img_in_Diff',
                                   on_delete=models.CASCADE)
    diff_percent = models.DecimalField(max_digits=6, decimal_places=5, default=0)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.diff_img_file.name
