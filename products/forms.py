from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image']


class RestockForm(forms.Form):
    name = forms.CharField(max_length=255)
    stock = forms.IntegerField(min_value=1, label='Stock to Add')