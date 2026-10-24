from django.contrib import admin
from .models import Coupon, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'subtotal', 'discount_amount', 'total_price', 'created_at')
    list_filter = ('status',)
    search_fields = ('id', 'user__username', 'full_name')
    inlines = [OrderItemInline]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'min_order_amount', 'active', 'times_used', 'usage_limit', 'valid_until')
    list_editable = ('active',)
    list_filter = ('active', 'discount_type')
