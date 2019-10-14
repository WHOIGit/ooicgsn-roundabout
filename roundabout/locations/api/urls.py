from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from .views import LocationViewSet

# Create a router and register our viewsets with it.
router = SimpleRouter()
router.register(r'locations', LocationViewSet )

urlpatterns = [
    path('', include(router.urls) ),
]
