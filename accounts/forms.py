from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from core.forms import BootstrapFormMixin
from .models import CustomUser

class SignupForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 'profile_picture']
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}
