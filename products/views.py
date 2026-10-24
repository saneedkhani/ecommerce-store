from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from core.utils import redirect_back
from .forms import ProductForm, RestockForm, ReviewForm
from .models import Category, Product, Review, WishlistItem, user_can_review

SORT_OPTIONS = {
    'newest': ('Newest', ['-created_at']),
    'price_asc': ('Price: low to high', ['effective_price']),
    'price_desc': ('Price: high to low', ['-effective_price']),
    'rating': ('Top rated', [F('avg_rating').desc(nulls_last=True), '-review_count']),
    'name': ('Name A-Z', ['name']),
}


def product_list(request, category_slug=None):
    products = (Product.objects.with_ratings().select_related('category')
                .annotate(effective_price=Coalesce('sale_price', 'price')))
    category = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    q = request.GET.get('q', '').strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q))

    min_price, max_price = request.GET.get('min_price', ''), request.GET.get('max_price', '')
    if min_price.isdigit():
        products = products.filter(effective_price__gte=min_price)
    if max_price.isdigit():
        products = products.filter(effective_price__lte=max_price)
    if request.GET.get('on_sale'):
        products = products.filter(sale_price__isnull=False)
    if request.GET.get('in_stock'):
        products = products.filter(stock__gt=0)

    sort = request.GET.get('sort', 'newest')
    if sort not in SORT_OPTIONS:
        sort = 'newest'
    products = products.order_by(*SORT_OPTIONS[sort][1])

    page = Paginator(products, 12).get_page(request.GET.get('page'))
    return render(request, 'products/product_list.html', {
        'page_obj': page,
        'category': category,
        'categories': Category.objects.all(),
        'q': q,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
        'sort_options': {key: label for key, (label, _) in SORT_OPTIONS.items()},
    })


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.with_ratings().select_related('category'), pk=pk)
    reviews = product.reviews.select_related('user')
    can_review = user_can_review(request.user, product)
    already_reviewed = request.user.is_authenticated and reviews.filter(user=request.user).exists()

    related = (Product.objects.with_ratings().filter(category=product.category).exclude(pk=product.pk)[:4]
               if product.category else [])
    rating_breakdown = []
    for stars in range(5, 0, -1):
        count = reviews.filter(rating=stars).count()
        percent = round(count / product.reviews_total * 100) if product.reviews_total else 0
        rating_breakdown.append({'stars': stars, 'count': count, 'percent': percent})

    return render(request, 'products/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'review_form': ReviewForm() if can_review and not already_reviewed else None,
        'can_review': can_review,
        'already_reviewed': already_reviewed,
        'related': related,
        'rating_breakdown': rating_breakdown,
    })


@login_required
@require_POST
def add_review(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if not user_can_review(request.user, product):
        messages.error(request, 'You can review a product after your order for it has been paid.')
    elif Review.objects.filter(product=product, user=request.user).exists():
        messages.info(request, 'You have already reviewed this product.')
    else:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Thanks for your review!')
        else:
            messages.error(request, 'Please choose a star rating.')
    return redirect('products:product_detail', pk=pk)


@login_required
def wishlist(request):
    items = request.user.wishlist.select_related('product', 'product__category')
    return render(request, 'products/wishlist.html', {'items': items})


@login_required
@require_POST
def toggle_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
    in_wishlist = created

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'in_wishlist': in_wishlist, 'count': request.user.wishlist.count()})
    messages.success(request, f'"{product.name}" {"added to" if in_wishlist else "removed from"} your wishlist.')
    return redirect_back(request, 'products:wishlist')


@staff_member_required
def add_or_restock_product(request):
    add_form = ProductForm(prefix='add')
    restock_form = RestockForm(prefix='restock')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_new':
            add_form = ProductForm(request.POST, request.FILES, prefix='add')
            if add_form.is_valid():
                product = add_form.save()
                messages.success(request, f'"{product.name}" was added.')
                return redirect('core:staff_products')

        elif action == 'restock':
            restock_form = RestockForm(request.POST, prefix='restock')
            if restock_form.is_valid():
                product = restock_form.cleaned_data['product']
                product.stock += restock_form.cleaned_data['stock']
                product.save(update_fields=['stock'])
                messages.success(request, f'"{product.name}" now has {product.stock} in stock.')
                return redirect('core:staff_products')

    return render(request, 'products/add_product.html', {
        'add_form': add_form,
        'restock_form': restock_form,
    })


@staff_member_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{product.name}" was updated.')
        return redirect('core:staff_products')
    return render(request, 'products/edit_product.html', {'form': form, 'product': product})


@staff_member_required
@require_POST
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f'"{name}" was deleted.')
    return redirect('core:staff_products')
