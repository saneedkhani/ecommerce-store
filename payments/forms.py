from django import forms
from core.forms import BootstrapFormMixin
from .models import Payment

class PaymentProofForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['bank_reference', 'proof_screenshot']
        labels = {'bank_reference': 'Transaction reference / ID', 'proof_screenshot': 'Payment screenshot'}

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('bank_reference') and not cleaned.get('proof_screenshot'):
            raise forms.ValidationError('Please enter the transaction reference or upload a screenshot.')
        return cleaned
