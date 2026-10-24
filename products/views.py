from django.shortcuts import render, get_object_or_404,redirect
from .models import Product

from django.contrib.auth.decorators import login_required
from .forms import ProductForm, RestockForm

@login_required
def add_or_restock_product(request):
    add_form = ProductForm(prefix='add')
    restock_form = RestockForm(prefix='restock')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_new':
            add_form = ProductForm(request.POST, request.FILES, prefix='add')
            if add_form.is_valid():
                name = add_form.cleaned_data['name']
                if Product.objects.filter(name=name).exists():
                    add_form.add_error('name', 'A product with this name already exists. Use Restock instead.')
                else:
                    add_form.save()
                    return redirect('products:product_list')

        elif action == 'restock':
            restock_form = RestockForm(request.POST, prefix='restock')
            if restock_form.is_valid():
                name = restock_form.cleaned_data['name']
                quantity = restock_form.cleaned_data['stock']
                existing = Product.objects.filter(name=name).first()
                if existing:
                    existing.stock += quantity
                    existing.save()
                    return redirect('products:product_list')
                else:
                    restock_form.add_error('name', 'No existing product found with this name.')

    return render(request, 'products/add_product.html', {
        'add_form': add_form,
        'restock_form': restock_form,
    })


def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})