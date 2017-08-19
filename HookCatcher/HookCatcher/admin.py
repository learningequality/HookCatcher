from django.contrib import admin

# Register your models here.
from .models import PR, Commit, Diff, History, Image, State


# display the UUID field in the django admin
class StateAdmin(admin.ModelAdmin):
    readonly_fields = ('state_uuid',)


class ImageAdmin(admin.ModelAdmin):
    readonly_fields = ('img_file',)


class DiffAdmin(admin.ModelAdmin):
    readonly_fields = ('diff_img_file',)


class HistoryAdmin(admin.ModelAdmin):
    readonly_fields = ('time',)


admin.site.register(State, StateAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Diff)
admin.site.register(Commit)
admin.site.register(PR)
admin.site.register(History, HistoryAdmin)
