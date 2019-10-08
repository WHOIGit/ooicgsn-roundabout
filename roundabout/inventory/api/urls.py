from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from .views import InventoryViewSet

# Create a router and register our viewsets with it.
router = SimpleRouter()
router.register(r'inventory', InventoryViewSet, 'inventory' )

urlpatterns = [
    path('', include(router.urls) ),
]
