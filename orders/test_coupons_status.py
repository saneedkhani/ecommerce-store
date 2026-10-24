from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from products.models import Product
from .models import Coupon, Order

User = get_user_model()
SHIPPING = {'full_name': 'C', 'address': 'A', 'phone_number': '1'}


class CouponTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('cust', password='x')
        self.product = Product.objects.create(name='Bag', price=4000, stock=10)
        Coupon.objects.create(code='welcome10', discount_type=Coupon.PERCENT, value=10)
        Coupon.objects.create(code='SAVE500', discount_type=Coupon.FIXED, value=500, min_order_amount=5000)
        self.client.force_authenticate(self.user)
        self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 1})

    def test_code_saved_uppercase_and_label(self):
        coupon = Coupon.objects.get(code='WELCOME10')
        self.assertEqual(coupon.label, '10% off')

    def test_checkout_with_coupon(self):
        response = self.client.post('/api/orders/checkout/', {**SHIPPING, 'coupon_code': 'welcome10'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['subtotal'], '4000.00')
        self.assertEqual(response.data['discount_amount'], '400.00')
        self.assertEqual(response.data['total_price'], '3600.00')
        self.assertEqual(Coupon.objects.get(code='WELCOME10').times_used, 1)

    def test_minimum_order_amount(self):
        response = self.client.post('/api/orders/check-coupon/', {'code': 'SAVE500'})
        self.assertEqual(response.status_code, 400)
        self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 1})  # now Rs. 8000
        response = self.client.post('/api/orders/check-coupon/', {'code': 'SAVE500'})
        self.assertEqual(response.data['total'], '7500.00')

    def test_expired_inactive_and_used_up(self):
        Coupon.objects.create(code='OLD', value=5, valid_until=timezone.now() - timedelta(days=1))
        Coupon.objects.create(code='OFF', value=5, active=False)
        Coupon.objects.create(code='ONCE', value=5, usage_limit=1, times_used=1)
        for code in ['OLD', 'OFF', 'ONCE', 'NOPE']:
            response = self.client.post('/api/orders/checkout/', {**SHIPPING, 'coupon_code': code})
            self.assertEqual(response.status_code, 400, code)
        self.assertEqual(Order.objects.count(), 0)

    def test_coupon_on_website_cart_and_checkout(self):
        self.client.force_login(self.user)
        self.client.post('/cart/coupon/apply/', {'code': 'WELCOME10'})
        self.assertEqual(self.client.session['coupon_code'], 'WELCOME10')
        summary = self.client.get('/cart/').context['summary']
        self.assertEqual(summary['discount'], Decimal('400.00'))
        self.client.post('/orders/checkout/', SHIPPING)
        self.assertEqual(Order.objects.get().total_price, Decimal('3600.00'))
        self.assertNotIn('coupon_code', self.client.session)


class OrderStatusTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('cust', password='x')
        self.staff = User.objects.create_user('staff', password='x', is_staff=True)
        self.product = Product.objects.create(name='Pen', price=100, stock=5)
        self.client.force_authenticate(self.user)
        self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 2})
        self.order_id = self.client.post('/api/orders/checkout/', SHIPPING).data['id']

    def stock(self):
        self.product.refresh_from_db()
        return self.product.stock

    def test_customer_cancels_pending_order(self):
        response = self.client.post(f'/api/orders/{self.order_id}/cancel/')
        self.assertEqual(response.data['status'], 'cancelled')
        self.assertEqual(self.stock(), 5)
        self.assertEqual(self.client.post(f'/api/orders/{self.order_id}/cancel/').status_code, 400)

    def test_staff_moves_order_through_timeline(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(f'/api/orders/{self.order_id}/status/', {'status': 'shipped'})
        self.assertEqual(response.data['status'], 'shipped')
        steps = {step['key']: step['done'] for step in response.data['timeline']}
        self.assertEqual(steps, {'pending': True, 'processing': True, 'shipped': True, 'delivered': False})

    def test_customer_cannot_set_status(self):
        response = self.client.post(f'/api/orders/{self.order_id}/status/', {'status': 'delivered'})
        self.assertEqual(response.status_code, 403)

    def test_staff_status_from_dashboard_and_cancel_restocks_once(self):
        self.client.force_login(self.staff)
        url = f'/dashboard/orders/{self.order_id}/status/'
        self.client.post(url, {'status': 'cancelled'})
        self.client.post(url, {'status': 'cancelled'})
        self.assertEqual(Order.objects.get(id=self.order_id).status, 'cancelled')
        self.assertEqual(self.stock(), 5)

    def test_order_pages(self):
        self.client.force_login(self.user)
        for url in ['/orders/history/', f'/orders/{self.order_id}/', f'/orders/success/{self.order_id}/',
                    f'/payments/submit/{self.order_id}/', '/accounts/profile/']:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_profile_update_prefills_checkout(self):
        self.client.force_login(self.user)
        self.client.post('/accounts/profile/', {'first_name': 'Sana', 'last_name': 'Ali', 'email': 's@example.test',
                                                'phone_number': '0300', 'address': 'Street 5'})
        self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 1})
        form = self.client.get('/orders/checkout/').context['form']
        self.assertEqual(form.initial['full_name'], 'Sana Ali')
        self.assertEqual(form.initial['address'], 'Street 5')
