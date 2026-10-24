from django.db import transaction
from cart.models import Cart
from products.models import Product
from .models import Order, OrderItem


class CheckoutError(Exception):
    """Raised when the cart can't be turned into an order (empty cart or not enough stock)."""


def place_order(user, full_name, address, phone_number):
    """Turn the user's cart into an order, deduct stock and empty the cart.

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

        order = Order.objects.create(
            user=user,
            full_name=full_name,
            address=address,
            phone_number=phone_number,
            total_price=sum(products[i.product_id].price * i.quantity for i in items),
        )

        for item in items:
            product = products[item.product_id]
            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.price,
                quantity=item.quantity
            )
            product.stock -= item.quantity
            product.save(update_fields=['stock'])

        cart.items.all().delete()  # clear cart after order placed

    return order
