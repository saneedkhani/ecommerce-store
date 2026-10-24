from django import forms
from core.forms import BootstrapFormMixin
from .models import Order

class CheckoutForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'address', 'phone_number']
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}


class CouponForm(BootstrapFormMixin, forms.Form):
    code = forms.CharField(max_length=30, label='Coupon code')


class OrderStatusForm(BootstrapFormMixin, forms.Form):
    status = forms.ChoiceField(choices=Order.STATUS_CHOICES)
