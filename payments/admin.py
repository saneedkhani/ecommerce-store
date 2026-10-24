from django.contrib import admin
from .models import Payment
from .services import set_payment_status

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'status', 'created_at')
    list_filter = ('status',)
    actions = ['mark_verified']

    def mark_verified(self, request, queryset):
        for payment in queryset.select_related('order'):
            set_payment_status(payment, 'verified')
    mark_verified.short_description = "Mark selected payments as verified"