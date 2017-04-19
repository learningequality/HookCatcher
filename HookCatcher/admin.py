from django.contrib import admin

# Register your models here.
from .models import PR, Commit, Diff, Image, State


# display the UUID field in the django admin
class StateAdmin(admin.ModelAdmin):
    readonly_fields = ('stateUUID',)


admin.site.register(State, StateAdmin)
admin.site.register(Image)
admin.site.register(Diff)
admin.site.register(Commit)
admin.site.register(PR)
