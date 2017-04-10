from __future__ import unicode_literals

from decimal import Decimal

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


# Create your models here.
@python_2_unicode_compatible
class Commit(models.Model):
    gitHash = models.CharField(max_length=200)

    def __str__(self):
        return '%s' % (self.gitHash)


@python_2_unicode_compatible
class State(models.Model):
    stateName = models.CharField(max_length=200)
    stateDesc = models.TextField()
    stateUrl = models.TextField()
    gitRepo = models.CharField(max_length=200)
    gitBranch = models.CharField(max_length=200)
    gitCommit = models.ForeignKey(Commit, on_delete=models.CASCADE)  # many commits for one state

    def __str__(self):
        return '%s, %s:%s %s' % (self.stateName,
                                 self.gitRepo,
                                 self.gitBranch,
                                 self.gitCommit.gitHash[:7])


@python_2_unicode_compatible
class PR(models.Model):
    gitRepo = models.CharField(max_length=200)
    gitPRNumber = models.IntegerField()
    # BASE of the git pull request Before version of state
    gitTargetCommit = models.ForeignKey(Commit, related_name='asTargetPR',
                                        on_delete=models.CASCADE)
    # HEAD of the git pull request After version of state
    gitSourceCommit = models.ForeignKey(Commit, related_name='asSourcePR',
                                        on_delete=models.CASCADE)

    def __str__(self):
        return '%s: PR #%d' % (self.gitRepo, self.gitPRNumber)


@python_2_unicode_compatible
class Image(models.Model):
    imgName = models.CharField(max_length=200)
    browserType = models.CharField(max_length=200)
    operatingSystem = models.CharField(max_length=200)
    width = models.IntegerField(null=True)      # int width of image
    height = models.IntegerField(null=True)     # int width of height
    # many Images to one State (for multiple browsers)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    def __str__(self):
        return 'img_%s, %s:%s %s' % (self.state.stateName,
                                     self.state.gitRepo,
                                     self.state.gitBranch,
                                     self.state.gitCommit.gitHash[:7])


@python_2_unicode_compatible
class Diff(models.Model):
    # GITHUB BASE of a PR (before state), many Diffs to one Image
    targetImg = models.ForeignKey(Image, related_name='asTargetDiff',
                                  on_delete=models.CASCADE)
    # GITHUB HEAD of a PR (after state)
    sourceImg = models.ForeignKey(Image, related_name='asSourceDiff',
                                  on_delete=models.CASCADE)
    diffImgName = models.CharField(max_length=200)
    diffPercent = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal('0.00'))

    def __str__(self):
        return '%s DIFF %s' % (self.sourceImg, self.targetImg)
