from django.db import transaction
from django.db.models import F
from cart.models import Cart
from products.models import Product
from .models import Coupon, Order, OrderItem


class CheckoutError(Exception):
    """Raised when the cart can't be turned into an order (empty cart, not enough stock, bad coupon)."""


class CouponError(CheckoutError):
    """Raised when a coupon code can't be used."""


def get_coupon(code, subtotal, lock=False):
    """Return the Coupon for this code if it can be used on this subtotal, otherwise raise CouponError."""
    coupons = Coupon.objects.select_for_update() if lock else Coupon.objects
    coupon = coupons.filter(code__iexact=(code or '').strip()).first()
    if coupon is None:
        raise CouponError('That coupon code does not exist.')
    problem = coupon.problem_with(subtotal)
    if problem:
        raise CouponError(problem)
    return coupon


def cart_summary(cart, coupon_code=None):
    """Subtotal, discount and total for showing the cart. An invalid coupon is reported, not raised."""
    subtotal = cart.total_price()
    summary = {'subtotal': subtotal, 'discount': 0, 'total': subtotal, 'coupon': None, 'coupon_error': None}
    if coupon_code:
        try:
            coupon = get_coupon(coupon_code, subtotal)
        except CouponError as error:
            summary['coupon_error'] = str(error)
        else:
            summary['coupon'] = coupon
            summary['discount'] = coupon.discount_for(subtotal)
            summary['total'] = subtotal - summary['discount']
    return summary


def place_order(user, full_name, address, phone_number, coupon_code=None):
    """Turn the user's cart into an order, apply the coupon, deduct stock and empty the cart.

    Shared by the website checkout and the REST API.
    """
    cart, created = Cart.objects.get_or_create(user=user)

    with transaction.atomic():
        items = list(cart.items.all())
        if not items:
            raise CheckoutError('Your cart is empty.')

        # lock the products so two customers can't buy the last item at the same time
        products = Product.objects.select_for_update().in_bulk([item.product_id for item in items])

        for item in items:
            product = products[item.product_id]
            if item.quantity > product.stock:
                raise CheckoutError(f'Only {product.stock} of "{product.name}" left. Please update your cart.')

        subtotal = sum(products[i.product_id].current_price * i.quantity for i in items)
        coupon = get_coupon(coupon_code, subtotal, lock=True) if coupon_code else None
        discount = coupon.discount_for(subtotal) if coupon else 0

        order = Order.objects.create(
            user=user,
            full_name=full_name,
            address=address,
            phone_number=phone_number,
            subtotal=subtotal,
            discount_amount=discount,
            coupon=coupon,
            coupon_code=coupon.code if coupon else '',
            total_price=subtotal - discount,
        )

        for item in items:
            product = products[item.product_id]
            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.current_price,
                quantity=item.quantity
            )
            product.stock -= item.quantity
            product.save(update_fields=['stock'])

        if coupon:
            Coupon.objects.filter(pk=coupon.pk).update(times_used=F('times_used') + 1)

        cart.items.all().delete()  # clear cart after order placed

    return order


def set_order_status(order, new_status):
    """Staff changes an order's status. Cancelling puts the items back in stock (only once)."""
    valid = dict(Order.STATUS_CHOICES)
    if new_status not in valid:
        raise ValueError(f'Invalid order status: {new_status}')

    with transaction.atomic():
        if new_status == 'cancelled' and order.status != 'cancelled':
            restock_order(order)
        order.status = new_status
        order.save()
    return order


def restock_order(order):
    for item in order.items.select_related('product'):
        if item.product:
            Product.objects.filter(pk=item.product.pk).update(stock=F('stock') + item.quantity)
