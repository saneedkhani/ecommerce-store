from django import forms
from .models import Payment

class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['bank_reference', 'proof_screenshot']