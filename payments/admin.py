from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'status', 'created_at')
    list_filter = ('status',)
    actions = ['mark_verified']

    def mark_verified(self, request, queryset):
        queryset.update(status='verified')
        for payment in queryset:
            payment.order.status = 'processing'
            payment.order.save()
    mark_verified.short_description = "Mark selected payments as verified"