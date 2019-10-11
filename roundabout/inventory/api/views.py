from rest_framework import generics, viewsets, filters
from ..models import Inventory
from .serializers import InventorySerializer


class InventoryViewSet(viewsets.ModelViewSet):
    serializer_class = InventorySerializer
    search_fields = ['serial_number']
    filter_backends = (filters.SearchFilter,)

    def get_queryset(self):
        queryset = Inventory.objects.all()
        # Set up eager loading to avoid N+1 selects
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset
