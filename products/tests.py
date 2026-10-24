from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from .models import Product

User = get_user_model()


class ProductApiTests(APITestCase):
    def setUp(self):
        Product.objects.create(name='Red Shoe', price='50.00', stock=3)
        Product.objects.create(name='Blue Hat', price='15.00', stock=10)

    def test_anyone_can_list_products(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

    def test_search_and_ordering(self):
        response = self.client.get('/api/products/?search=shoe')
        self.assertEqual([p['name'] for p in response.data['results']], ['Red Shoe'])
        response = self.client.get('/api/products/?ordering=price')
        self.assertEqual(response.data['results'][0]['name'], 'Blue Hat')

    def test_customer_cannot_create_product(self):
        self.client.force_authenticate(User.objects.create_user('cust', password='x'))
        response = self.client.post('/api/products/', {'name': 'Hack', 'price': '1.00', 'stock': 1})
        self.assertEqual(response.status_code, 403)

    def test_staff_can_create_product(self):
        self.client.force_authenticate(User.objects.create_user('staff', password='x', is_staff=True))
        response = self.client.post('/api/products/', {'name': 'Green Bag', 'price': '30.00', 'stock': 5})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Product.objects.filter(name='Green Bag').exists())


class ProductPageTests(APITestCase):
    def test_add_product_page_is_staff_only(self):
        self.client.force_login(User.objects.create_user('cust', password='x'))
        self.assertEqual(self.client.get('/products/add/').status_code, 302)
