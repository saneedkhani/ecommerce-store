from django.db.models import F
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from .models import Category, Product, Review, WishlistItem, user_can_review
from .serializers import CategorySerializer, ProductSerializer, ReviewSerializer, WishlistItemSerializer


class IsStaffOrReadOnly(permissions.BasePermission):
    """Anyone can read; only staff can create, edit or delete."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user.is_staff


@extend_schema(tags=['Products'])
class CategoryViewSet(viewsets.ModelViewSet):
    """Product categories (staff can manage them)."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]
    pagination_class = None


@extend_schema(tags=['Products'], parameters=[
    OpenApiParameter('category', str, description='Category slug, e.g. electronics'),
    OpenApiParameter('min_price', float, description='Minimum current price'),
    OpenApiParameter('max_price', float, description='Maximum current price'),
    OpenApiParameter('on_sale', bool, description='Only discounted products'),
    OpenApiParameter('in_stock', bool, description='Only products in stock'),
    OpenApiParameter('featured', bool, description='Only featured products'),
])
class ProductViewSet(viewsets.ModelViewSet):
    """Product catalogue. Supports `?search=`, the filters below and
    `?ordering=effective_price` (current price) / `-effective_price` / `-avg_rating` / `name` / `-created_at`."""
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['effective_price', 'price', 'name', 'created_at', 'avg_rating']

    def get_queryset(self):
        products = (Product.objects.with_ratings().select_related('category')
                    .annotate(effective_price=Coalesce('sale_price', 'price')).order_by('-created_at'))
        params = self.request.query_params
        if params.get('category'):
            products = products.filter(category__slug=params['category'])
        if params.get('min_price'):
            products = products.filter(effective_price__gte=params['min_price'])
        if params.get('max_price'):
            products = products.filter(effective_price__lte=params['max_price'])
        if params.get('on_sale') in ('1', 'true', 'True'):
            products = products.filter(sale_price__isnull=False, sale_price__lt=F('price'))
        if params.get('in_stock') in ('1', 'true', 'True'):
            products = products.filter(stock__gt=0)
        if params.get('featured') in ('1', 'true', 'True'):
            products = products.filter(is_featured=True)
        return products

    @extend_schema(methods=['GET'], responses=ReviewSerializer(many=True))
    @extend_schema(methods=['POST'], request=ReviewSerializer, responses={201: ReviewSerializer})
    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticatedOrReadOnly],
            serializer_class=ReviewSerializer, pagination_class=None)
    def reviews(self, request, pk=None):
        """List a product's reviews, or post one (only after a paid order containing the product)."""
        product = self.get_object()
        if request.method == 'GET':
            return Response(ReviewSerializer(product.reviews.select_related('user'), many=True).data)

        if not user_can_review(request.user, product):
            raise PermissionDenied('You can review a product after your order for it has been paid.')
        if product.reviews.filter(user=request.user).exists():
            raise ValidationError({'detail': 'You have already reviewed this product.'})
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Wishlist'])
class WishlistViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):
    """The logged-in user's wishlist. DELETE uses the wishlist item id."""
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # schema generation has no logged-in user
            return WishlistItem.objects.none()
        return WishlistItem.objects.filter(user=self.request.user).select_related('product', 'product__category')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item, created = WishlistItem.objects.get_or_create(user=request.user, product=serializer.validated_data['product'])
        return Response(self.get_serializer(item).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
