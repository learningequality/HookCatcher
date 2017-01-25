from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from decimal import Decimal
import uuid
# Create your models here.

@python_2_unicode_compatible
class State(models.Model):
	id = models.AutoField(primary_key=True)
	state_name = models.CharField(max_length=200)
	state_desc = models.TextField()
	state_json = models.TextField()
	github_source_type = models.CharField(max_length=200)
	github_source_id = models.CharField(max_length=200)
	def __str__(self):
		return self.state_name


@python_2_unicode_compatible
class Image(models.Model):
	id = models.AutoField(primary_key=True)
	state_img_url = models.URLField(max_length=200)	
	browser_type = models.CharField(max_length=200)
	state = models.ForeignKey(State, on_delete=models.CASCADE)#many Images to one State (for multiple browsers)
	def __str__(self):
		return '%s_img%s' % (self.state.state_name, self.state.id)


@python_2_unicode_compatible
class Diff(models.Model):
	id = models.AutoField(primary_key=True)
	test_state_img = models.ForeignKey(Image, related_name='where_isTest', on_delete=models.CASCADE)#many Diffs to one Image
	control_state_img = models.ForeignKey(Image, related_name='where_isControl', on_delete=models.CASCADE)#many Diffs to one Image
	diff_img_url = models.URLField(max_length=200)
	diff_percent = models.DecimalField(max_digits=6,decimal_places=3,default=Decimal('0.00'))
	def __str__(self):
		return '%s diff %s' % (self.test_state_img, self.control_state_img)
