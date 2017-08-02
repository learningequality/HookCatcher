from __future__ import unicode_literals

import os
import uuid
from decimal import Decimal

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


# Create your models here.
@python_2_unicode_compatible
class Commit(models.Model):
    git_repo = models.CharField(max_length=200)
    git_branch = models.CharField(max_length=200)
    git_hash = models.CharField(unique=True, max_length=200)

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


    def __str__(self):
        return '%s, %s:%s %s' % (self.state_name,
                                 self.git_commit.git_repo,
                                 self.git_commit.git_branch,
                                 self.git_commit.git_hash[:7])


@python_2_unicode_compatible
class PR(models.Model):
    git_repo = models.CharField(max_length=200)
    git_pr_number = models.IntegerField(unique=True)
    # BASE of the git pull request Before version of state
    # call state.gitCommit.targetCommit_set.all() to get PR's where state is used as a target
    git_target_commit = models.ForeignKey(Commit, related_name='target_commit_in_PR',
                                          on_delete=models.CASCADE)
    # HEAD of the git pull request After version of state
    git_source_commit = models.ForeignKey(Commit, related_name='source_commit_in_PR',
                                          on_delete=models.CASCADE)
    # add a commit hash of the merged version of the head and base
    git_pr_commit = models.ForeignKey(Commit, null=True, related_name='merge_commit_in_PR',
                                      on_delete=models.CASCADE)


    def __str__(self):
        return '%s: PR #%d' % (self.git_repo, self.git_pr_number)


@python_2_unicode_compatible
class Image(models.Model):
    img_file = models.ImageField(upload_to='img', max_length=2000, null=True, blank=True)
    browser_type = models.CharField(max_length=200)
    operating_system = models.CharField(max_length=200) 
    device_res_width = models.IntegerField()
    device_res_height = models.IntegerField()
    # many Images to one State (for multiple browsers)
    state = models.ForeignKey(State, on_delete=models.CASCADE)


    def __str__(self):
        # if the img_file doesn't exist and therefore has no file name, print so
        if self.img_file == None or self.img_file.name == '':
            # for the case when the image is not done loading yet
            return 'Image File is Currently Processing...'
        else:
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


    def __str__(self):
        return self.diff_img_file.name
