from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def backfill_created_events(apps, schema_editor):
    """Give every pre-existing Revision a synthetic "created" history row so the
    Revision History section is populated for legacy data. User is unknown."""
    Revision = apps.get_model("parts", "Revision")
    RevisionEvent = apps.get_model("parts", "RevisionEvent")
    events = [
        RevisionEvent(
            revision=revision,
            event_type="created",
            user=None,
            created_at=revision.created_at,
        )
        for revision in Revision.objects.all().iterator()
    ]
    RevisionEvent.objects.bulk_create(events, batch_size=500)


def remove_all_events(apps, schema_editor):
    apps.get_model("parts", "RevisionEvent").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("parts", "0020_part_bulk_upload_event"),
    ]

    operations = [
        migrations.CreateModel(
            name="RevisionEvent",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "revision",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="revision_events",
                        to="parts.revision",
                    ),
                ),
                (
                    "event_type",
                    models.CharField(
                        choices=[("created", "created"), ("updated", "updated")],
                        db_index=True,
                        default="created",
                        max_length=20,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="revision_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("detail", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["created_at", "id"],
                "get_latest_by": "created_at",
            },
        ),
        migrations.RunPython(backfill_created_events, remove_all_events),
    ]
