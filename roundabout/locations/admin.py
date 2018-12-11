from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Location

# Register your models here.


admin.site.register(Location, MPTTModelAdmin)