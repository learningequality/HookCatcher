from django.contrib import admin

# Register your models here.
from .models import State, Image, Diff

admin.site.register(State)
admin.site.register(Image)
admin.site.register(Diff)