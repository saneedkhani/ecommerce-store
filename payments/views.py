from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from orders.models import Order
from .models import Payment
from .forms import PaymentProofForm
from .services import set_payment_status, STAFF_STATUSES

BANK_DETAILS = {
    'account_title': 'Your Store Name',
    'account_number': 'PK00XXXX0000000000000000',
    'bank_name': 'Your Bank',
}

@login_required
def submit_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # one payment per order: don't let the customer submit again
    if Payment.objects.filter(order=order).exists():
        return redirect('payments:payment_submitted', order_id=order.id)

    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.user = request.user
            payment.save()
            return redirect('payments:payment_submitted', order_id=order.id)
    else:
        form = PaymentProofForm()

    return render(request, 'payments/submit_payment.html', {
        'form': form, 'order': order, 'bank_details': BANK_DETAILS
    })


@login_required
def payment_submitted(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'payments/payment_submitted.html', {'order': order})


@staff_member_required
def payment_dashboard(request):
    payments = Payment.objects.all().order_by('-created_at')  # show ALL, not just pending
    return render(request, 'payments/dashboard.html', {'payments': payments})


@staff_member_required
def pending_count(request):
    count = Payment.objects.filter(status='pending').count()
    return JsonResponse({'count': count})


@staff_member_required
def update_payment_status(request, payment_id, new_status):
    payment = get_object_or_404(Payment, id=payment_id)

    if new_status in STAFF_STATUSES:
        set_payment_status(payment, new_status)

    return redirect('payments:dashboard')