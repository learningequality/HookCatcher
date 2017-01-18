from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from decimal import Decimal
import uuid
# Create your models here.

@python_2_unicode_compatible
class State(models.Model):
	id = models.AutoField(primary_key=True)
	state_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
	state_name = models.CharField(max_length=200)
	state_desc = models.TextField()
	state_json = models.TextField()
	target = models.CharField(max_length=200)
	target_type = models.CharField(max_length=200)
	target_id = models.CharField(max_length=200)
	def __str__(self):
		return self.state_name

@python_2_unicode_compatible
class Diff(models.Model):
	id = models.AutoField(primary_key=True)
	before = models.CharField(max_length=200)
	after = models.CharField(max_length=200)
	url = models.URLField(max_length=200)
	diff_percent = models.DecimalField(max_digits=6,decimal_places=3,default=Decimal('0.00'))
	def __str__(self):
		return '%s diff %s' % (self.before, self.after)

@python_2_unicode_compatible
class Image(models.Model):
	id = models.AutoField
	url = models.URLField(max_length=200)
	browser = models.CharField(max_length=200)
	state = models.ForeignKey(State, on_delete=models.CASCADE)
	def __str__(self):
		return '%s_img' % self.state.state_name


