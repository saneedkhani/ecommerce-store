from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer, CartItemUpdateSerializer


def check_stock(product, quantity):
    if quantity > product.stock:
        raise ValidationError({'quantity': f'Only {product.stock} of "{product.name}" in stock.'})


@extend_schema(tags=['Cart'])
class CartView(APIView):
    """The logged-in user's cart."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def get_cart(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def get(self, request):
        return Response(CartSerializer(self.get_cart(), context={'request': request}).data)

    @extend_schema(responses={204: None})
    def delete(self, request):
        """Remove every item from the cart."""
        self.get_cart().items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Cart'])
class CartItemViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Add, change or remove items in the logged-in user's cart."""
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['post', 'patch', 'delete']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # schema generation has no logged-in user
            return CartItem.objects.none()
        return CartItem.objects.filter(cart__user=self.request.user).select_related('product')

    def get_serializer_class(self):
        return CartItemUpdateSerializer if self.action == 'partial_update' else CartItemSerializer

    def create(self, request, *args, **kwargs):
        """Add a product to the cart. If it's already there, the quantity is increased."""
        serializer = CartItemSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']

        cart, created = Cart.objects.get_or_create(user=request.user)
        item = CartItem.objects.filter(cart=cart, product=product).first()
        quantity = serializer.validated_data['quantity'] + (item.quantity if item else 0)
        check_stock(product, quantity)

        if item:
            item.quantity = quantity
            item.save()
        else:
            item = CartItem.objects.create(cart=cart, product=product, quantity=quantity)
        return Response(CartItemSerializer(item, context={'request': request}).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=CartItemSerializer)
    def partial_update(self, request, *args, **kwargs):
        """Set a new quantity for a cart item."""
        item = self.get_object()
        serializer = CartItemUpdateSerializer(item, data=request.data)
        serializer.is_valid(raise_exception=True)
        check_stock(item.product, serializer.validated_data['quantity'])
        serializer.save()
        return Response(CartItemSerializer(item, context={'request': request}).data)
