from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from cart.models import Cart
from products.models import Product
from .models import Order, OrderItem
from .forms import CheckoutForm

@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)

    if not cart.items.exists():
        return redirect('cart:cart_detail')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                items = list(cart.items.all())
                # lock the products so two customers can't buy the last item at the same time
                products = Product.objects.select_for_update().in_bulk([item.product_id for item in items])

                for item in items:
                    product = products[item.product_id]
                    if item.quantity > product.stock:
                        messages.error(request, f'Only {product.stock} of "{product.name}" left. Please update your cart.')
                        return redirect('cart:cart_detail')

                order = form.save(commit=False)
                order.user = request.user
                order.total_price = sum(products[i.product_id].price * i.quantity for i in items)
                order.save()

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
            return redirect('orders:order_success', order_id=order.id)
    else:
        form = CheckoutForm()

    return render(request, 'orders/checkout.html', {'form': form, 'cart': cart})


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})