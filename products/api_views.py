from drf_spectacular.utils import extend_schema
from rest_framework import permissions, viewsets
from .models import Product
from .serializers import ProductSerializer


class IsStaffOrReadOnly(permissions.BasePermission):
    """Anyone can read; only staff can create, edit or delete."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user.is_staff


@extend_schema(tags=['Products'])
class ProductViewSet(viewsets.ModelViewSet):
    """Product catalogue. Supports `?search=`, `?ordering=price` / `-price` / `name` / `-created_at` and `?page=`."""
    queryset = Product.objects.order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name', 'created_at']
