from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import MooringPart
from roundabout.locations.models import Location
from roundabout.parts.models import Part

# Register your models here
admin.site.register(MooringPart, MPTTModelAdmin)
