from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Printer)
admin.site.register(TempImport)
admin.site.register(TempImportItem)
