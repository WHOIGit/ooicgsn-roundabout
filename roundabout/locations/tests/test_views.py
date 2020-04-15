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

from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User, Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from roundabout.locations import views
from roundabout.locations.models import Location


class LocationDetailTests(TestCase):

    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpass'
        User = get_user_model()
        content_type = ContentType.objects.get_for_model(Location)
        self.permission = Permission.objects.get(content_type=content_type, codename='add_location')
        group_name = "admin_test"
        self.group = Group(name=group_name)
        self.group.save()
        self.user = User.objects.create_user(self.username, password=self.password, is_active=True)

    def tearDown(self):
        self.user.delete()
        self.group.delete()

    def test_home_view_wrong_user_access(self):
        """user with NO location permission should not have access
        """
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('locations:locations_home'))
        assert response.status_code == 403

    def test_home_view_can_access(self):
        """user in location permission should have access
        """
        self.user.groups.add(self.group)
        self.user.user_permissions.add(self.permission)
        self.user.save()
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('locations:locations_home'))
        assert response.status_code == 200
