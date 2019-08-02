# Generated by Django 2.2.1 on 2019-06-19 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assemblies', '0003_assemblypart_assembly'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssemblyType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
