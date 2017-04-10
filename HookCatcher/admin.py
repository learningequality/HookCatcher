from django.contrib import admin

# Register your models here.
from .models import PR, Commit, Diff, Image, State

admin.site.register(State)
admin.site.register(Image)
admin.site.register(Diff)
admin.site.register(Commit)
admin.site.register(PR)
