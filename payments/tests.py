from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from orders.models import Order
from products.models import Product

User = get_user_model()


class PaymentApiTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user('cust', password='x')
        self.staff = User.objects.create_user('staff', password='x', is_staff=True)
        self.product = Product.objects.create(name='Shoe', price='20.00', stock=3)

        self.client.force_authenticate(self.customer)
        self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 2})
        self.order_id = self.client.post('/api/orders/checkout/', {
            'full_name': 'C', 'address': 'A', 'phone_number': '1'}).data['id']

    def submit_payment(self):
        return self.client.post(f'/api/orders/{self.order_id}/payment/', {'bank_reference': 'TXN123'})

    def test_customer_submits_payment_once(self):
        response = self.submit_payment()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(self.submit_payment().status_code, 400)

    def test_payment_needs_reference_or_screenshot(self):
        response = self.client.post(f'/api/orders/{self.order_id}/payment/', {})
        self.assertEqual(response.status_code, 400)

    def test_customer_cannot_list_payments(self):
        self.assertEqual(self.client.get('/api/payments/').status_code, 403)

    def test_staff_verifies_payment(self):
        payment_id = self.submit_payment().data['id']
        self.client.force_authenticate(self.staff)
        response = self.client.post(f'/api/payments/{payment_id}/status/', {'status': 'verified'})
        self.assertEqual(response.data['status'], 'verified')
        self.assertEqual(Order.objects.get(id=self.order_id).status, 'processing')

    def test_reject_cancels_order_and_restores_stock_once(self):
        payment_id = self.submit_payment().data['id']
        self.client.force_authenticate(self.staff)
        self.client.post(f'/api/payments/{payment_id}/status/', {'status': 'rejected'})
        self.client.post(f'/api/payments/{payment_id}/status/', {'status': 'rejected'})
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(Order.objects.get(id=self.order_id).status, 'cancelled')

    def test_invalid_status_rejected(self):
        payment_id = self.submit_payment().data['id']
        self.client.force_authenticate(self.staff)
        response = self.client.post(f'/api/payments/{payment_id}/status/', {'status': 'pending'})
        self.assertEqual(response.status_code, 400)


class DashboardTests(APITestCase):
    def test_shipped_orders_count_in_revenue(self):
        user = User.objects.create_user('cust', password='x')
        Order.objects.create(user=user, full_name='C', address='A', phone_number='1',
                             total_price='40.00', status='shipped')
        self.client.force_login(User.objects.create_user('staff', password='x', is_staff=True))
        response = self.client.get('/dashboard/')
        self.assertEqual(response.context['total_revenue'], Decimal('40.00'))
