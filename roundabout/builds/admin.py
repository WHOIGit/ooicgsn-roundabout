from django.contrib import admin

from .models import Build, BuildAction

# Register your models here
admin.site.register(Build)

admin.site.register(BuildAction)
