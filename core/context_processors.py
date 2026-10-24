from django.db.models import Sum
from cart.models import CartItem
from products.models import Category


def shop(request):
    """Data every page needs: categories for the menu, cart count and wishlist ids for the header."""
    context = {'nav_categories': Category.objects.all(), 'cart_count': 0, 'wishlist_ids': set()}
    user = request.user
    if user.is_authenticated:
        context['cart_count'] = CartItem.objects.filter(cart__user=user).aggregate(n=Sum('quantity'))['n'] or 0
        context['wishlist_ids'] = set(user.wishlist.values_list('product_id', flat=True))
    return context
