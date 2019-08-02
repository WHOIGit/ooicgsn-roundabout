from django.contrib import admin

from .models import Assembly, AssemblyPart, AssemblyType, AssemblyDocument

# Register your models here
admin.site.register(Assembly)

admin.site.register(AssemblyPart)

admin.site.register(AssemblyType)

admin.site.register(AssemblyDocument)
