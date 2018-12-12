from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Part, PartType, Documentation
from roundabout.locations.models import Location

# Register your models here
admin.site.register(Documentation)

admin.site.register(PartType, MPTTModelAdmin)

admin.site.register(Part)
