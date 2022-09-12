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

from django.urls import path

from . import views
from . import user_search
from . import change_search

app_name = "search"
urlpatterns = [
    path("searchbar", view=views.searchbar_redirect, name="searchbar"),
    path("inventory", view=views.InventoryTableView.as_view(), name="inventory"),
    path(
        "calibrations", view=views.CalibrationTableView.as_view(), name="calibrations"
    ),
    path(
        "configconsts", view=views.ConfigConstTableView.as_view(), name="configconsts"
    ),
    path("builds", view=views.BuildTableView.as_view(), name="build"),
    path("parts", view=views.PartTableView.as_view(), name="part"),
    path("assembly", view=views.AssemblyTableView.as_view(), name="assembly"),
    path("actions", view=views.ActionTableView.as_view(), name="action"),
    path("user", view=user_search.UserSearchView.as_view(), name="user"),
    path("change", view=change_search.ChangeSearchView.as_view(), name="change"),
    path("tests", view=views.InventoryTestResultTableView.as_view(), name="tests"),
]
