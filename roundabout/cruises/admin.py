from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import Cruise, Vessel

@admin.register(Cruise)
class CruiseAdmin(ImportExportModelAdmin):
    pass

@admin.register(Vessel)
class VesselAdmin(ImportExportModelAdmin):
    pass
