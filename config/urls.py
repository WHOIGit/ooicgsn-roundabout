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

from django.conf import settings
from django.urls import include, path, re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults as default_views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path(
        "users/",
        include("roundabout.users.urls", namespace="users"),
    ),
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
    path('locations/', include('roundabout.locations.urls', namespace='locations')),
    path('parts/', include('roundabout.parts.urls', namespace='parts')),
    path('inventory/', include('roundabout.inventory.urls', namespace='inventory')),
    path('deployments/', include('roundabout.inventory.urls_deployment', namespace='deployments')),
    path('admintools/', include('roundabout.admintools.urls', namespace='admintools')),
    path('userdefinedfields/', include('roundabout.userdefinedfields.urls', namespace='userdefinedfields')),
    path('assemblies/', include('roundabout.assemblies.urls', namespace='assemblies')),
    path('builds/', include('roundabout.builds.urls', namespace='builds')),
    path('cruises/', include('roundabout.cruises.urls', namespace='cruises')),
    path('reports/', include('roundabout.reports.urls', namespace='reports')),
    path('search/', include('roundabout.search.urls', namespace='search')),
    path('export/', include('roundabout.exports.urls', namespace='export')),
    path('calibrations/', include('roundabout.calibrations.urls', namespace='calibrations')),
    path('configs_constants/', include('roundabout.configs_constants.urls', namespace='configs_constants')),
    path('field_instances/', include('roundabout.field_instances.urls', namespace='field_instances')),
    # API urls
    path('api/v1/', include('roundabout.inventory.api.urls')),
    path('api/v1/', include('roundabout.locations.api.urls')),
    path('api/v1/', include('roundabout.parts.api.urls')),
    path('api/v1/', include('roundabout.assemblies.api.urls')),
    path('api/v1/', include('roundabout.userdefinedfields.api.urls')),
    # API JWT token paths
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    #Summernote WYSIWYG
    path('summernote/', include('django_summernote.urls')),
] + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
