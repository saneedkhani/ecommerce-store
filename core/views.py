from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from products.models import Product
from orders.models import Order
from payments.models import Payment

def home(request):
    products = Product.objects.all()[:8]
    return render(request, 'core/home.html', {'products': products})


@staff_member_required
def admin_dashboard(request):
    context = {
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'total_revenue': sum(o.total_price for o in Order.objects.filter(status__in=['processing', 'delivered'])),
        'pending_payments': Payment.objects.filter(status='pending').count(),
        'low_stock_products': Product.objects.filter(stock__lt=5),
        'recent_orders': Order.objects.order_by('-created_at')[:5],
    }
    return render(request, 'core/admin_dashboard.html', context)