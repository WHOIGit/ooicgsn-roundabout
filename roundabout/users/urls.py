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
from roundabout.users.views import (
    user_list_view,
    user_redirect_view,
    user_update_view,
    user_detail_view,
)

app_name = "users"
urlpatterns = [
    path('admin/<int:pk>/', view=views.UserAdminDetailView.as_view(), name='user_admin_detail'),
    path('admin/add/', view=views.UserAdminCreateView.as_view(), name='user_admin_add'),
    path('admin/edit/<int:pk>/', view=views.UserAdminUpdateView.as_view(), name='user_admin_update'),
    path('admin/edit/password/<int:pk>/', view=views.UserAdminPasswordChangeView.as_view(), name='user_admin_change_password'),
    path('admin/delete/<int:pk>/', view=views.UserAdminDeleteView.as_view(), name='user_admin_delete'),
    # Base User paths from Allauth
    path("", view=user_list_view, name="list"),
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]
