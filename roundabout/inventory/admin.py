from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from .models import Inventory, Deployment, Action

# Register your models here.
admin.site.register(Inventory, MPTTModelAdmin)
admin.site.register(Deployment)
admin.site.register(Action)
