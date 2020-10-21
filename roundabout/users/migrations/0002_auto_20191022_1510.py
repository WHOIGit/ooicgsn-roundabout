"""
# Copyright (C) 2019-2020 Woods Hole Oceanographic Institution
#
# This file is part of the Roundabout Database project ("RDB" or
# "ooicgsn-roundabout").
#
# ooicgsn-roundabout is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# ooicgsn-roundabout is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ooicgsn-roundabout in the COPYING.md file at the project root.
# If not, see <http://www.gnu.org/licenses/>.
"""

# Generated by Django 2.2.4 on 2019-10-22 15:10
import environ
from django.contrib.auth.hashers import make_password
from django.db import migrations

env = environ.Env()

def generate_superuser(apps, schema_editor):

    User = apps.get_model('users', 'User')
    Group = apps.get_model('auth','Group')

    DJANGO_SU_NAME = env('DJANGO_SU_NAME')
    DJANGO_SU_EMAIL = env('DJANGO_SU_EMAIL')
    DJANGO_SU_PASSWORD = make_password(env('DJANGO_SU_PASSWORD'))

    superuser = User.objects.create(
        username=DJANGO_SU_NAME,
        email=DJANGO_SU_EMAIL,
        password=DJANGO_SU_PASSWORD,
        is_superuser=True,
        is_staff=True,
        is_active=True,
    )

    superuser.save()

    # Add superuser to the "admin" group
    group = Group.objects.get(name='admin')
    superuser.groups.add(group)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(generate_superuser),
    ]
