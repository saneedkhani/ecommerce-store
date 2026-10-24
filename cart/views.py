from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from core.utils import redirect_back
from orders.forms import CouponForm
from orders.services import cart_summary, get_coupon, CouponError
from products.models import Product
from .models import Cart, CartItem

COUPON_SESSION_KEY = 'coupon_code'


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.stock < 1:
        messages.error(request, f'Sorry, "{product.name}" is out of stock.')
        return redirect('products:product_detail', pk=product.id)

    try:
        wanted = max(int(request.POST.get('quantity', 1)), 1)
    except (TypeError, ValueError):
        wanted = 1

    cart, created = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 0})
    new_quantity = min(item.quantity + wanted, product.stock)
    if new_quantity < item.quantity + wanted:
        messages.warning(request, f'Only {product.stock} of "{product.name}" in stock.')
    else:
        messages.success(request, f'"{product.name}" added to your cart.')
    item.quantity = new_quantity
    item.save()

    if request.POST.get('buy_now'):
        return redirect('orders:checkout')
    if request.method == 'POST':
        return redirect_back(request, 'cart:cart_detail')
    return redirect('cart:cart_detail')


@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product', 'product__category')
    summary = cart_summary(cart, request.session.get(COUPON_SESSION_KEY))
    if summary['coupon_error']:
        messages.warning(request, f"Coupon removed: {summary['coupon_error']}")
        request.session.pop(COUPON_SESSION_KEY, None)
    return render(request, 'cart/cart_detail.html', {
        'cart': cart, 'items': items, 'summary': summary, 'coupon_form': CouponForm(),
    })


@login_required
@require_POST
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.info(request, f'"{item.product.name}" removed from your cart.')
    return redirect('cart:cart_detail')


@login_required
def update_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            messages.error(request, 'Please enter a valid quantity.')
            return redirect('cart:cart_detail')

        if quantity > 0:
            if quantity > item.product.stock:
                quantity = item.product.stock
                messages.warning(request, f'Only {quantity} of "{item.product.name}" in stock.')
            item.quantity = quantity
            item.save()
        else:
            item.delete()
    return redirect('cart:cart_detail')


@login_required
@require_POST
def apply_coupon(request):
    form = CouponForm(request.POST)
    if form.is_valid():
        cart, created = Cart.objects.get_or_create(user=request.user)
        try:
            coupon = get_coupon(form.cleaned_data['code'], cart.total_price())
        except CouponError as error:
            messages.error(request, str(error))
        else:
            request.session[COUPON_SESSION_KEY] = coupon.code
            messages.success(request, f'Coupon {coupon.code} applied: {coupon.label}.')
    return redirect('cart:cart_detail')


@login_required
@require_POST
def remove_coupon(request):
    request.session.pop(COUPON_SESSION_KEY, None)
    messages.info(request, 'Coupon removed.')
    return redirect('cart:cart_detail')
