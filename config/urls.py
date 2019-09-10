from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults as default_views

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
    path('moorings/', include('roundabout.moorings.urls', namespace='moorings')),
    path('inventory/', include('roundabout.inventory.urls', namespace='inventory')),
    path('deployments/', include('roundabout.inventory.urls_deployment', namespace='deployments')),
    path('admintools/', include('roundabout.admintools.urls', namespace='admintools')),
    path('userdefinedfields/', include('roundabout.userdefinedfields.urls', namespace='userdefinedfields')),
    path('assemblies/', include('roundabout.assemblies.urls', namespace='assemblies')),
    path('builds/', include('roundabout.builds.urls', namespace='builds')),
    path('reports/', include('roundabout.reports.urls', namespace='reports')),
    path('search/', include('roundabout.search.urls', namespace='search')),
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
