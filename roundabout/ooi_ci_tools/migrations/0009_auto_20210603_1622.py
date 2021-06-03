# Generated by Django 3.1.3 on 2021-06-03 16:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assemblies', '0011_auto_20201117_2030'),
        ('inventory', '0068_auto_20210512_1446'),
        ('parts', '0017_merge_20210209_1909'),
        ('ooi_ci_tools', '0008_auto_20210527_1840'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='referencedesignator',
            options={'ordering': ['name']},
        ),
        migrations.RemoveField(
            model_name='referencedesignator',
            name='approved',
        ),
        migrations.RemoveField(
            model_name='referencedesignator',
            name='assembly_part',
        ),
        migrations.RemoveField(
            model_name='referencedesignator',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='referencedesignator',
            name='deployment',
        ),
        migrations.RemoveField(
            model_name='referencedesignator',
            name='detail',
        ),
        migrations.RemoveField(
            model_name='referencedesignator',
            name='inventory',
        ),
        migrations.RemoveField(
            model_name='referencedesignator',
            name='part',
        ),
        migrations.RemoveField(
            model_name='referencedesignator',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='referencedesignator',
            name='user_approver',
        ),
        migrations.RemoveField(
            model_name='referencedesignator',
            name='user_draft',
        ),
        migrations.CreateModel(
            name='ReferenceDesignatorEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved', models.BooleanField(choices=[(True, 'Approved'), (False, 'Draft')], default=False)),
                ('detail', models.TextField(blank=True)),
                ('assembly_part', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assemblypart_referencedesignatorevents', to='assemblies.assemblypart')),
                ('deployment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deployment_referencedesignatorevents', to='inventory.deployment')),
                ('inventory', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inventory_referencedesignatorevents', to='inventory.inventory')),
                ('part', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='part_referencedesignatorevents', to='parts.part')),
                ('user_approver', models.ManyToManyField(related_name='approver_referencedesignatorevents', to=settings.AUTH_USER_MODEL)),
                ('user_draft', models.ManyToManyField(blank=True, related_name='reviewer_referencedesignatorevents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='referencedesignator',
            name='refdes_event',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reference_designators', to='ooi_ci_tools.referencedesignatorevent'),
        ),
    ]
