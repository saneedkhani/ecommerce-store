from django.db import transaction
from orders.services import restock_order

# statuses staff can set (a new payment starts as 'pending')
STAFF_STATUSES = ['verified', 'rejected', 'not_received']


def set_payment_status(payment, new_status):
    """Update a payment and its order. Shared by the staff dashboard and the REST API.

    verified     -> order becomes 'processing'
    rejected     -> order becomes 'cancelled' and its items go back in stock
    not_received -> order stays as it is while staff investigate
    """
    if new_status not in STAFF_STATUSES:
        raise ValueError(f'Invalid payment status: {new_status}')

    with transaction.atomic():
        payment.status = new_status
        payment.save()

        order = payment.order
        if new_status == 'verified':
            order.status = 'processing'
        elif new_status == 'rejected' and order.status != 'cancelled':
            order.status = 'cancelled'
            restock_order(order)  # put the items back in stock
        order.save()

    return payment
