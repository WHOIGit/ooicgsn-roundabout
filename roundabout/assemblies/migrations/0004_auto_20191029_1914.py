"""
Auto-generate default Assembly Types for start up
"""
from django.db import migrations
from django.apps import apps

AssemblyType = apps.get_model('assemblies', 'AssemblyType')

def create_assembly_types(apps, schema_editor):
    assembly_types = ['AUV', 'Glider', 'Mooring', 'ROV', 'HOV', 'Towed Vehicle']

    for assembly_type in assembly_types:
        obj, created = AssemblyType.objects.get_or_create(name=assembly_type)


class Migration(migrations.Migration):

    dependencies = [
        ('assemblies', '0003_auto_20191022_1758'),
    ]

    operations = [
        migrations.RunPython(create_assembly_types),
    ]
