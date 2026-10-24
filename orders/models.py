from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.utils import timezone
from products.models import Product


class Coupon(models.Model):
    PERCENT = 'percent'
    FIXED = 'fixed'
    TYPE_CHOICES = [(PERCENT, 'Percentage (%)'), (FIXED, 'Fixed amount (Rs.)')]

    code = models.CharField(max_length=30, unique=True)
    discount_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=PERCENT)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text='Leave empty for unlimited')
    times_used = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def problem_with(self, subtotal):
        """Return why the coupon can't be used for this subtotal, or None if it's valid."""
        now = timezone.now()
        if not self.active:
            return 'This coupon is no longer active.'
        if self.valid_from and now < self.valid_from:
            return 'This coupon is not valid yet.'
        if self.valid_until and now > self.valid_until:
            return 'This coupon has expired.'
        if self.usage_limit is not None and self.times_used >= self.usage_limit:
            return 'This coupon has reached its usage limit.'
        if subtotal < self.min_order_amount:
            return f'Spend at least Rs. {self.min_order_amount} to use this coupon.'
        return None

    def discount_for(self, subtotal):
        if self.discount_type == self.PERCENT:
            discount = subtotal * self.value / Decimal(100)
        else:
            discount = self.value
        return min(discount, subtotal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def label(self):
        value = f'{self.value.normalize():,f}'  # 10.00 -> 10
        return f'{value}% off' if self.discount_type == self.PERCENT else f'Rs. {value} off'

    def __str__(self):
        return f'{self.code} ({self.label})'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    STATUS_FLOW = ['pending', 'processing', 'shipped', 'delivered']
    STATUS_COLORS = {'pending': 'warning', 'processing': 'info', 'shipped': 'primary',
                     'delivered': 'success', 'cancelled': 'danger'}

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    coupon_code = models.CharField(max_length=30, blank=True)  # kept even if the coupon is deleted
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self.status, 'secondary')

    def timeline(self):
        """Steps for the order-tracking bar: [{'key', 'label', 'done', 'current'}]."""
        labels = dict(self.STATUS_CHOICES)
        position = self.STATUS_FLOW.index(self.status) if self.status in self.STATUS_FLOW else -1
        return [{'key': key, 'label': labels[key], 'done': i <= position, 'current': i == position}
                for i, key in enumerate(self.STATUS_FLOW)]

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # price at time of purchase
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'}"
