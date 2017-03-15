from __future__ import unicode_literals

from decimal import Decimal

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


# Create your models here.

@python_2_unicode_compatible
class State(models.Model):
    stateName = models.CharField(max_length=200)
    stateDesc = models.TextField()
    stateJson = models.TextField()
    gitSourceType = models.CharField(max_length=200)  # PR or BRANCH
    # if Branch then branch name, if PR then PR number
    gitSourceName = models.CharField(max_length=200)
    gitCommit = models.CharField(max_length=200)  # unique ID of the git tree for this state

    def __str__(self):
        return '%s %s_%s' % (self.stateName, self.gitSourceType, self.gitSourceName)


@python_2_unicode_compatible
class Image(models.Model):
    stateImgUrl = models.CharField(max_length=200)
    browserType = models.CharField(max_length=200)
    operatingSystem = models.CharField(max_length=200)
    width = models.IntegerField(null=True)  # int width of image
    height = models.IntegerField(null=True)  # int width of height
    # many Images to one State (for multiple browsers)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    def __str__(self):
        return 'img_%s_%s_%s' % (self.state.stateName,
                                 self.state.gitSourceType,
                                 self.state.gitSourceName)


@python_2_unicode_compatible
class Diff(models.Model):
    # GITHUB BASE FORK many Diffs to one Image
    beforeStateImg = models.ForeignKey(Image, related_name='whereBeforeState',
                                       on_delete=models.CASCADE)
    # many Diffs to one Image (resutltingBASEFORK after merging/PR)
    afterStateImg = models.ForeignKey(Image, related_name='whereAfterState',
                                      on_delete=models.CASCADE)
    diffImgUrl = models.CharField(max_length=200)
    diffPercent = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal('0.00'))

    def __str__(self):
        return '%s DIFF %s' % (self.beforeStateImg, self.afterStateImg)
