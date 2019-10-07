from rest_framework import generics, viewsets, filters
from ..models import Inventory
from .serializers import InventorySerializer


class InventoryViewSet(viewsets.ModelViewSet):

    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    search_fields = ['serial_number']
    filter_backends = (filters.SearchFilter,)
