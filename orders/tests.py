from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from products.models import Product
from .models import Order

User = get_user_model()
SHIPPING = {'full_name': 'Cust Omer', 'address': '1 Main St', 'phone_number': '0300000000'}


class CheckoutApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('cust', password='x')
        self.client.force_authenticate(self.user)
        self.product = Product.objects.create(name='Shoe', price='20.00', stock=3)

    def add_to_cart(self, quantity):
        self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': quantity})

    def test_checkout_creates_order_and_deducts_stock(self):
        self.add_to_cart(2)
        response = self.client.post('/api/orders/checkout/', SHIPPING)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['total_price'], '40.00')
        self.assertEqual(response.data['status'], 'pending')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        self.assertEqual(self.client.get('/api/cart/').data['item_count'], 0)

    def test_checkout_with_empty_cart_fails(self):
        self.assertEqual(self.client.post('/api/orders/checkout/', SHIPPING).status_code, 400)

    def test_checkout_fails_if_stock_dropped(self):
        self.add_to_cart(3)
        Product.objects.filter(id=self.product.id).update(stock=1)
        response = self.client.post('/api/orders/checkout/', SHIPPING)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_customers_only_see_their_own_orders(self):
        self.add_to_cart(1)
        order_id = self.client.post('/api/orders/checkout/', SHIPPING).data['id']
        self.assertEqual(self.client.get('/api/orders/').data['count'], 1)

        self.client.force_authenticate(User.objects.create_user('other', password='x'))
        self.assertEqual(self.client.get('/api/orders/').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/orders/{order_id}/').status_code, 404)

        self.client.force_authenticate(User.objects.create_user('staff', password='x', is_staff=True))
        self.assertEqual(self.client.get('/api/orders/').data['count'], 1)


class HomePageTests(APITestCase):
    def test_home_page_at_root(self):
        self.assertEqual(self.client.get('/').status_code, 200)
