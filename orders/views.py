from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from cart.models import Cart
from cart.views import COUPON_SESSION_KEY
from .models import Order
from .forms import CheckoutForm
from .services import cart_summary, place_order, set_order_status, CheckoutError, CouponError

@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)

    if not cart.items.exists():
        messages.info(request, 'Your cart is empty.')
        return redirect('cart:cart_detail')

    coupon_code = request.session.get(COUPON_SESSION_KEY)
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = place_order(request.user, coupon_code=coupon_code, **form.cleaned_data)
            except CouponError as error:
                request.session.pop(COUPON_SESSION_KEY, None)
                messages.error(request, f'Coupon removed: {error}')
                return redirect('cart:cart_detail')
            except CheckoutError as error:
                messages.error(request, str(error))
                return redirect('cart:cart_detail')
            request.session.pop(COUPON_SESSION_KEY, None)
            return redirect('orders:order_success', order_id=order.id)
    else:
        user = request.user
        form = CheckoutForm(initial={  # pre-fill from the saved profile
            'full_name': user.get_full_name() or user.username,
            'address': user.address or '',
            'phone_number': user.phone_number or '',
        })

    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart': cart,
        'items': cart.items.select_related('product'),
        'summary': cart_summary(cart, coupon_code),
    })


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items').select_related('payment')
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    page = Paginator(orders, 10).get_page(request.GET.get('page'))
    return render(request, 'orders/order_history.html', {
        'page_obj': page, 'status': status, 'status_choices': Order.STATUS_CHOICES,
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related('payment'), id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'items': order.items.select_related('product'),
        'payment': getattr(order, 'payment', None),
    })


@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != 'pending':
        messages.error(request, 'Only pending orders can be cancelled. Please contact support.')
    else:
        set_order_status(order, 'cancelled')
        messages.success(request, f'Order #{order.id} was cancelled.')
    return redirect('orders:order_detail', order_id=order.id)
