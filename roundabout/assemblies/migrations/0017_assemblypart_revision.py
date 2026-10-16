from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("parts", "0020_part_bulk_upload_event"),
        ("assemblies", "0016_auto_20221121_2151"),
    ]

    operations = [
        migrations.AddField(
            model_name="assemblypart",
            name="revision",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assembly_parts",
                to="parts.revision",
            ),
        ),
    ]
