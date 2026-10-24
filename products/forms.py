from django import forms
from core.forms import BootstrapFormMixin
from .models import Product, Review


class ProductForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'sale_price', 'stock', 'image', 'is_featured']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}
        labels = {'is_featured': 'Show on home page (featured)'}


class RestockForm(BootstrapFormMixin, forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.order_by('name'))
    stock = forms.IntegerField(min_value=1, label='Stock to add')


class ReviewForm(BootstrapFormMixin, forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(i, f'{i} star{"s" if i > 1 else ""}') for i in range(5, 0, -1)], coerce=int)

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'What did you like or dislike?'})}
