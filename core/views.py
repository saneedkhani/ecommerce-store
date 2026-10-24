import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from products.models import Category, Product
from orders.forms import OrderStatusForm
from orders.models import Order, OrderItem
from orders.services import set_order_status
from payments.models import Payment
from .utils import redirect_back

PAID_STATUSES = ['processing', 'shipped', 'delivered']


def home(request):
    products = Product.objects.with_ratings().select_related('category')
    context = {
        'hero': products.filter(is_featured=True).exclude(image='').first() or products.exclude(image='').first(),
        'featured': products.filter(is_featured=True)[:8],
        'on_sale': [p for p in products.filter(sale_price__isnull=False) if p.on_sale][:4],
        'new_arrivals': products.order_by('-created_at')[:8],
        'categories': Category.objects.annotate(product_count=Count('products')),
    }
    return render(request, 'core/home.html', context)


@staff_member_required
def admin_dashboard(request):
    today = timezone.localdate()
    week_start = today - timedelta(days=6)
    paid_orders = Order.objects.filter(status__in=PAID_STATUSES)

    # revenue per day for the last 7 days (for the chart)
    daily = dict(paid_orders.filter(created_at__date__gte=week_start)
                 .annotate(day=TruncDate('created_at')).values('day')
                 .annotate(total=Sum('total_price')).values_list('day', 'total'))
    days = [week_start + timedelta(days=i) for i in range(7)]

    context = {
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'total_revenue': paid_orders.aggregate(total=Sum('total_price'))['total'] or 0,
        'pending_payments': Payment.objects.filter(status='pending').count(),
        'low_stock_products': Product.objects.filter(stock__lt=5).order_by('stock')[:6],
        'recent_orders': Order.objects.select_related('user').order_by('-created_at')[:6],
        'top_products': (OrderItem.objects.filter(order__status__in=PAID_STATUSES, product__isnull=False)
                         .values('product__name').annotate(sold=Sum('quantity')).order_by('-sold')[:5]),
        'chart_labels': json.dumps([d.strftime('%a') for d in days]),
        'chart_values': json.dumps([float(daily.get(d, 0) or 0) for d in days]),
    }
    return render(request, 'core/admin_dashboard.html', context)


@staff_member_required
def staff_orders(request):
    orders = Order.objects.select_related('user', 'payment').order_by('-created_at')
    status = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()
    if status:
        orders = orders.filter(status=status)
    if q:
        filters = Q(full_name__icontains=q) | Q(user__username__icontains=q)
        if q.lstrip('#').isdigit():
            filters |= Q(id=int(q.lstrip('#')))
        orders = orders.filter(filters)

    page = Paginator(orders, 15).get_page(request.GET.get('page'))
    return render(request, 'staff/orders.html', {
        'page_obj': page, 'status': status, 'q': q, 'status_choices': Order.STATUS_CHOICES,
        'status_counts': dict(Order.objects.values_list('status').annotate(n=Count('id'))),
    })


@staff_member_required
@require_POST
def staff_update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    form = OrderStatusForm(request.POST)
    if form.is_valid():
        set_order_status(order, form.cleaned_data['status'])
        messages.success(request, f'Order #{order.id} is now {order.get_status_display()}.')
    return redirect_back(request, 'core:staff_orders')


@staff_member_required
def staff_products(request):
    products = Product.objects.select_related('category').order_by('name')
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    if q:
        products = products.filter(name__icontains=q)
    if category:
        products = products.filter(category__slug=category)
    page = Paginator(products, 15).get_page(request.GET.get('page'))
    return render(request, 'staff/products.html', {
        'page_obj': page, 'q': q, 'category': category, 'categories': Category.objects.all(),
    })
