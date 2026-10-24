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


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'full_name', 'address', 'phone_number', 'status',
                  'total_price', 'payment_status', 'created_at', 'items']

    def get_payment_status(self, order) -> str | None:
        payment = getattr(order, 'payment', None)
        return payment.status if payment else None


class CheckoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['full_name', 'address', 'phone_number']
