from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from .views import PartViewSet

# Create a router and register our viewsets with it.
router = SimpleRouter()
router.register(r'parts', PartViewSet )

urlpatterns = [
    path('', include(router.urls) ),
]
