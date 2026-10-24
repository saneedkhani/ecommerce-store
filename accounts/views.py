from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import LoginForm, ProfileForm, SignupForm


def _next_url(request, default):
    target = request.POST.get('next') or request.GET.get('next')
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return target
    return default


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to ShopWave, {user.username}!')
            return redirect(_next_url(request, 'core:home'))
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect(_next_url(request, 'core:admin_dashboard' if user.is_staff else 'core:home'))
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:home')

@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your profile was updated.')
        return redirect('accounts:profile')

    orders = request.user.orders.all()
    return render(request, 'accounts/profile.html', {
        'form': form,
        'recent_orders': orders[:5],
        'order_count': orders.count(),
        'total_spent': orders.filter(status__in=['processing', 'shipped', 'delivered'])
                             .aggregate(total=Sum('total_price'))['total'] or 0,
        'wishlist_count': request.user.wishlist.count(),
        'review_count': request.user.reviews.count(),
    })


def admin_login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                return redirect('core:admin_dashboard')
            else:
                form.add_error(None, 'This login is for admin accounts only.')
    else:
        form = LoginForm()
    return render(request, 'accounts/admin_login.html', {'form': form})
