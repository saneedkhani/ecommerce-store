from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from cart.models import Cart
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
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = cart.total_price()
            order.save()

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )

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