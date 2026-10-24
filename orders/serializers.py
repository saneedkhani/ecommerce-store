from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'price', 'quantity', 'subtotal']

    def get_product_name(self, item) -> str:
        return item.product.name if item.product else 'Deleted Product'


class TimelineStepSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    done = serializers.BooleanField()
    current = serializers.BooleanField()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment_status = serializers.SerializerMethodField()
    timeline = TimelineStepSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'full_name', 'address', 'phone_number', 'status', 'subtotal', 'discount_amount',
                  'coupon_code', 'total_price', 'payment_status', 'timeline', 'created_at', 'updated_at', 'items']

    def get_payment_status(self, order) -> str | None:
        payment = getattr(order, 'payment', None)
        return payment.status if payment else None


class CheckoutSerializer(serializers.ModelSerializer):
    coupon_code = serializers.CharField(required=False, allow_blank=True, max_length=30)

    class Meta:
        model = Order
        fields = ['full_name', 'address', 'phone_number', 'coupon_code']


class CouponCheckSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=30)


class CouponResultSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
