from django.db import migrations, models


def copy_fk_to_m2m(apps, schema_editor):
    AssemblyPart = apps.get_model("assemblies", "AssemblyPart")
    for ap in AssemblyPart.objects.exclude(revision__isnull=True).iterator():
        ap.revisions.add(ap.revision_id)


def copy_m2m_to_fk(apps, schema_editor):
    AssemblyPart = apps.get_model("assemblies", "AssemblyPart")
    for ap in AssemblyPart.objects.filter(revisions__isnull=False).distinct().iterator():
        ap.revision_id = ap.revisions.first().id
        ap.save(update_fields=["revision"])


class Migration(migrations.Migration):

    dependencies = [
        ("parts", "0020_part_bulk_upload_event"),
        ("assemblies", "0017_assemblypart_revision"),
    ]

    operations = [
        migrations.AddField(
            model_name="assemblypart",
            name="revisions",
            field=models.ManyToManyField(
                blank=True, related_name="assembly_parts_tmp", to="parts.Revision"
            ),
        ),
        migrations.RunPython(copy_fk_to_m2m, copy_m2m_to_fk),
        migrations.RemoveField(model_name="assemblypart", name="revision"),
        migrations.AlterField(
            model_name="assemblypart",
            name="revisions",
            field=models.ManyToManyField(
                blank=True, related_name="assembly_parts", to="parts.Revision"
            ),
        ),
    ]
