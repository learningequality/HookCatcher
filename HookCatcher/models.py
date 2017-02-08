from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from decimal import Decimal
import uuid
# Create your models here.

@python_2_unicode_compatible
class State(models.Model):
	state_name = models.CharField(max_length=200)
	state_desc = models.TextField()
	state_json = models.TextField()
	git_source_type = models.CharField(max_length=200) # PR or BRANCH
	git_source_name = models.CharField(max_length=200) #if Branch then branch name, if PR then PR number
	git_commit = models.CharField(max_length=200) # unique ID of the git tree for this state
	def __str__(self):
		return '%s %s_%s' % (self.state_name, self.git_source_type, self.git_source_name)


@python_2_unicode_compatible
class Image(models.Model):
	state_img_url = models.URLField(max_length=200)	
	browser_type = models.CharField(max_length=200)
	operating_system = models.CharField(max_length=200)
	width = models.IntegerField(null=True)# int width of image
	height = models.IntegerField(null=True) # int width of height
	state = models.ForeignKey(State, on_delete=models.CASCADE)#many Images to one State (for multiple browsers)
	def __str__(self):
		return 'img_%s_%s_%s' % (self.state.state_name, self.state.git_source_type, self.state.git_source_name)


@python_2_unicode_compatible
class Diff(models.Model):
	before_state_img = models.ForeignKey(Image, related_name='isBeforeState', on_delete=models.CASCADE)#GITHUB BASE FORK many Diffs to one Image 
	after_state_img = models.ForeignKey(Image, related_name='isAfterState', on_delete=models.CASCADE)#many Diffs to one Image (resutltingBASEFORK after merging/PR)
	diff_img_url = models.URLField(max_length=200)
	diff_percent = models.DecimalField(max_digits=6,decimal_places=3,default=Decimal('0.00'))
	def __str__(self):
		return '%s DIFF %s' % (self.before_state_img, self.after_state_img)


