# Generated by Django 2.2.10 on 2020-04-21 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Vessel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vessel_name', models.CharField(max_length=100)),
                ('ICES_code', models.CharField(blank=True, max_length=10)),
                ('operator', models.CharField(blank=True, max_length=100)),
                ('call_sign', models.CharField(blank=True, max_length=10)),
                ('MMSI_number', models.IntegerField(null=True)),
                ('IMO_number', models.IntegerField(null=True)),
                ('length', models.DecimalField(decimal_places=1, max_digits=4, null=True)),
                ('max_speed', models.DecimalField(decimal_places=1, max_digits=3, null=True)),
                ('max_draft', models.DecimalField(decimal_places=1, max_digits=3, null=True)),
                ('designation', models.CharField(blank=True, max_length=10)),
                ('active', models.BooleanField(choices=[(True, 'Yes'), (False, 'No')], default=True, null=True)),
                ('R2R', models.BooleanField(choices=[(True, 'Yes'), (False, 'No')], default=True, null=True)),
            ],
            options={
                'ordering': ('vessel_name',),
            },
        ),
    ]
