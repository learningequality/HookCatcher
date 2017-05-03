from django.contrib import admin

# Register your models here.
from .models import PR, Commit, Diff, Image, State


# display the UUID field in the django admin
class StateAdmin(admin.ModelAdmin):
    readonly_fields = ('stateUUID',)


class ImageAdmin(admin.ModelAdmin):
    readonly_fields = ('imgName',)


admin.site.register(State, StateAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Diff)
admin.site.register(Commit)
admin.site.register(PR)
