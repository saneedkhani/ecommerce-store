from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from cart.models import Cart
from payments.models import Payment
from payments.serializers import PaymentSerializer
from .models import Order
from .serializers import (OrderSerializer, CheckoutSerializer, CouponCheckSerializer, CouponResultSerializer,
                          OrderStatusSerializer)
from .services import get_coupon, place_order, set_order_status, CheckoutError


@extend_schema(tags=['Orders'], parameters=[
    OpenApiParameter('status', str, description='Filter by order status, e.g. pending'),
])
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Customers see their own orders; staff see all orders."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ['created_at', 'total_price']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # schema generation has no logged-in user
            return Order.objects.none()
        orders = Order.objects.select_related('payment').prefetch_related('items__product').order_by('-created_at')
        if not self.request.user.is_staff:
            orders = orders.filter(user=self.request.user)
        if self.request.query_params.get('status'):
            orders = orders.filter(status=self.request.query_params['status'])
        return orders

    @extend_schema(request=CheckoutSerializer, responses={201: OrderSerializer})
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Place an order from everything in the cart, with an optional coupon. Stock is checked and deducted."""
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = place_order(request.user, **serializer.validated_data)
        except CheckoutError as error:
            raise ValidationError({'detail': str(error)})
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=CouponCheckSerializer, responses=CouponResultSerializer)
    @action(detail=False, methods=['post'], url_path='check-coupon')
    def check_coupon(self, request):
        """Preview a coupon on your current cart before checking out."""
        serializer = CouponCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart, created = Cart.objects.get_or_create(user=request.user)
        subtotal = cart.total_price()
        try:
            coupon = get_coupon(serializer.validated_data['code'], subtotal)
        except CheckoutError as error:
            raise ValidationError({'code': str(error)})
        discount = coupon.discount_for(subtotal)
        return Response(CouponResultSerializer({
            'code': coupon.code, 'label': coupon.label, 'subtotal': subtotal,
            'discount': discount, 'total': subtotal - discount}).data)

    @extend_schema(request=None, responses=OrderSerializer)
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel your own order while it is still pending. Items go back in stock."""
        order = self.get_object()
        if order.user != request.user:
            raise PermissionDenied('You can only cancel your own orders.')
        if order.status != 'pending':
            raise ValidationError({'detail': 'Only pending orders can be cancelled.'})
        set_order_status(order, 'cancelled')
        return Response(OrderSerializer(order).data)

    @extend_schema(request=OrderStatusSerializer, responses=OrderSerializer, tags=['Orders (staff)'])
    @action(detail=True, methods=['post'], url_path='status', permission_classes=[permissions.IsAdminUser])
    def set_status(self, request, pk=None):
        """Staff only: move an order to processing, shipped, delivered or cancelled."""
        order = self.get_object()
        serializer = OrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_order_status(order, serializer.validated_data['status'])
        return Response(OrderSerializer(order).data)

    @extend_schema(request=PaymentSerializer, responses={201: PaymentSerializer})
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def payment(self, request, pk=None):
        """Submit bank-transfer proof for your order (reference and/or screenshot)."""
        order = self.get_object()
        if order.user != request.user:
            raise PermissionDenied('You can only pay for your own orders.')
        if Payment.objects.filter(order=order).exists():
            raise ValidationError({'detail': 'A payment has already been submitted for this order.'})
        if order.status == 'cancelled':
            raise ValidationError({'detail': 'This order was cancelled.'})

        serializer = PaymentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(order=order, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
