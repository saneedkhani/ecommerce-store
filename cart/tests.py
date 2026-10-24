from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from products.models import Product

User = get_user_model()


class CartApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('cust', password='x')
        self.client.force_authenticate(self.user)
        self.product = Product.objects.create(name='Shoe', price='20.00', stock=3)

    def test_cart_requires_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/cart/').status_code, 401)

    def test_add_item_twice_increases_quantity(self):
        self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 1})
        self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 2})
        cart = self.client.get('/api/cart/').data
        self.assertEqual(cart['item_count'], 3)
        self.assertEqual(str(cart['total_price']), '60.00')

    def test_cannot_add_more_than_stock(self):
        response = self.client.post('/api/cart/items/', {'product_id': self.product.id, 'quantity': 4})
        self.assertEqual(response.status_code, 400)
        self.assertIn('quantity', response.data)

    def test_update_and_remove_item(self):
        item_id = self.client.post('/api/cart/items/', {'product_id': self.product.id}).data['id']
        response = self.client.patch(f'/api/cart/items/{item_id}/', {'quantity': 2})
        self.assertEqual(response.data['quantity'], 2)
        self.assertEqual(self.client.patch(f'/api/cart/items/{item_id}/', {'quantity': 9}).status_code, 400)
        self.assertEqual(self.client.delete(f'/api/cart/items/{item_id}/').status_code, 204)
        self.assertEqual(self.client.get('/api/cart/').data['item_count'], 0)

    def test_cannot_touch_another_users_cart_item(self):
        item_id = self.client.post('/api/cart/items/', {'product_id': self.product.id}).data['id']
        self.client.force_authenticate(User.objects.create_user('other', password='x'))
        self.assertEqual(self.client.delete(f'/api/cart/items/{item_id}/').status_code, 404)


class CartPageTests(APITestCase):
    def test_invalid_quantity_does_not_crash(self):
        user = User.objects.create_user('cust', password='x')
        product = Product.objects.create(name='Shoe', price='20.00', stock=3)
        self.client.force_login(user)
        self.client.get(f'/cart/add/{product.id}/')
        item = product.cartitem_set.get()
        response = self.client.post(f'/cart/update/{item.id}/', {'quantity': 'abc'})
        self.assertEqual(response.status_code, 302)
