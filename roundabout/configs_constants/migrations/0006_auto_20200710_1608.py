# Generated by Django 2.2.13 on 2020-07-10 16:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parts', '0008_merge_20200617_1450'),
        ('configs_constants', '0005_auto_20200710_1538'),
    ]

    operations = [
        migrations.AddField(
            model_name='constdefault',
            name='part',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='constant_defaults', to='parts.Part'),
        ),
        migrations.AlterUniqueTogether(
            name='constdefault',
            unique_together={('part', 'config_name')},
        ),
    ]
