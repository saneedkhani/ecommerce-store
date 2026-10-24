import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APITestCase

from orders.models import Order
from .models import Category, Product, Review, WishlistItem

User = get_user_model()
SHIPPING = {'full_name': 'C', 'address': 'A', 'phone_number': '1'}


class CatalogueTests(APITestCase):
    def setUp(self):
        self.tech = Category.objects.create(name='Electronics', icon='bi-laptop')
        self.books = Category.objects.create(name='Books')
        self.phone = Product.objects.create(name='Phone', category=self.tech, price=1000, sale_price=800, stock=5)
        self.laptop = Product.objects.create(name='Laptop', category=self.tech, price=5000, stock=0)
        self.novel = Product.objects.create(name='Novel', category=self.books, price=300, stock=9)

    def test_sale_price_helpers(self):
        self.assertTrue(self.phone.on_sale)
        self.assertEqual(self.phone.current_price, 800)
        self.assertEqual(self.phone.discount_percent, 20)
        self.assertFalse(self.novel.on_sale)
        self.assertEqual(self.novel.current_price, 300)

    def test_category_slug_created(self):
        self.assertEqual(self.tech.slug, 'electronics')
        self.assertEqual(self.client.get('/products/category/electronics/').status_code, 200)

    def test_shop_filters(self):
        def names(url):
            return [p.name for p in self.client.get(url).context['page_obj']]
        self.assertEqual(sorted(names('/products/category/books/')), ['Novel'])
        self.assertEqual(names('/products/?on_sale=1'), ['Phone'])
        self.assertNotIn('Laptop', names('/products/?in_stock=1'))
        self.assertEqual(names('/products/?min_price=500&max_price=900'), ['Phone'])  # uses sale price 800
        self.assertEqual(names('/products/?sort=price_asc'), ['Novel', 'Phone', 'Laptop'])
        self.assertEqual(names('/products/?q=nov'), ['Novel'])

    def test_api_filters_and_categories(self):
        response = self.client.get('/api/products/?category=electronics&ordering=effective_price')
        self.assertEqual([p['name'] for p in response.data['results']], ['Phone', 'Laptop'])
        self.assertEqual(response.data['results'][0]['current_price'], '800.00')
        self.assertEqual(self.client.get('/api/products/?on_sale=true').data['count'], 1)
        self.assertEqual(len(self.client.get('/api/categories/').data), 2)

    def test_sale_price_must_be_lower(self):
        self.client.force_authenticate(User.objects.create_user('staff', password='x', is_staff=True))
        response = self.client.post('/api/products/', {'name': 'Bad', 'price': '100', 'sale_price': '150', 'stock': 1})
        self.assertEqual(response.status_code, 400)

    def test_cart_and_order_use_sale_price(self):
        user = User.objects.create_user('cust', password='x')
        self.client.force_authenticate(user)
        self.client.post('/api/cart/items/', {'product_id': self.phone.id, 'quantity': 2})
        self.assertEqual(str(self.client.get('/api/cart/').data['total_price']), '1600.00')
        order = self.client.post('/api/orders/checkout/', SHIPPING).data
        self.assertEqual(order['total_price'], '1600.00')
        self.assertEqual(order['items'][0]['price'], '800.00')

    def test_pages_render(self):
        for url in ['/', '/products/', f'/products/{self.phone.id}/', '/products/?sort=rating']:
            self.assertEqual(self.client.get(url).status_code, 200, url)


class ReviewTests(APITestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Mug', price=500, stock=10)
        self.user = User.objects.create_user('cust', password='x')
        self.client.force_authenticate(self.user)

    def buy(self, status='processing'):
        order = Order.objects.create(user=self.user, full_name='C', address='A', phone_number='1',
                                     total_price=500, status=status)
        order.items.create(product=self.product, price=500, quantity=1)

    def test_cannot_review_without_paid_order(self):
        self.buy(status='pending')
        response = self.client.post(f'/api/products/{self.product.id}/reviews/', {'rating': 5})
        self.assertEqual(response.status_code, 403)

    def test_review_once_after_paid_order(self):
        self.buy()
        url = f'/api/products/{self.product.id}/reviews/'
        self.assertEqual(self.client.post(url, {'rating': 4, 'comment': 'Nice'}).status_code, 201)
        self.assertEqual(self.client.post(url, {'rating': 5}).status_code, 400)
        self.assertEqual(self.client.get(f'/api/products/{self.product.id}/').data['rating'], 4.0)

    def test_review_from_website(self):
        self.buy(status='delivered')
        self.client.force_login(self.user)
        self.client.post(f'/products/{self.product.id}/review/', {'rating': 5, 'comment': 'Great'})
        self.assertEqual(Review.objects.get().rating, 5)


class WishlistTests(APITestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Lamp', price=900, stock=3)
        self.user = User.objects.create_user('cust', password='x')

    def test_toggle_from_website_ajax(self):
        self.client.force_login(self.user)
        url = f'/products/{self.product.id}/wishlist/'
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.json(), {'in_wishlist': True, 'count': 1})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.json()['in_wishlist'], False)
        self.assertEqual(self.client.get('/products/wishlist/').status_code, 200)

    def test_wishlist_api(self):
        self.client.force_authenticate(self.user)
        item_id = self.client.post('/api/wishlist/', {'product_id': self.product.id}).data['id']
        self.assertEqual(self.client.post('/api/wishlist/', {'product_id': self.product.id}).status_code, 200)
        self.assertEqual(len(self.client.get('/api/wishlist/').data), 1)
        self.assertEqual(self.client.delete(f'/api/wishlist/{item_id}/').status_code, 204)
        self.assertFalse(WishlistItem.objects.exists())


class StaffPanelTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='x', is_staff=True)
        self.product = Product.objects.create(name='Chair', price=2000, stock=4)

    def test_staff_pages(self):
        self.client.force_login(self.staff)
        for url in ['/dashboard/', '/dashboard/orders/', '/dashboard/products/', '/payments/dashboard/',
                    '/products/add/', f'/products/{self.product.id}/edit/']:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_customers_cannot_open_staff_pages(self):
        self.client.force_login(User.objects.create_user('cust', password='x'))
        for url in ['/dashboard/', '/dashboard/orders/', '/dashboard/products/']:
            self.assertEqual(self.client.get(url).status_code, 302, url)

    def test_edit_and_delete_product(self):
        self.client.force_login(self.staff)
        self.client.post(f'/products/{self.product.id}/edit/', {
            'name': 'Chair', 'price': '2000', 'sale_price': '1500', 'stock': '4'})
        self.product.refresh_from_db()
        self.assertEqual(self.product.sale_price, Decimal('1500'))
        self.client.post(f'/products/{self.product.id}/delete/')
        self.assertFalse(Product.objects.exists())


class SeedCommandTests(APITestCase):
    def test_seed_demo_creates_catalogue(self):
        media = tempfile.mkdtemp()
        try:
            with override_settings(MEDIA_ROOT=media):
                call_command('seed_demo', verbosity=0)
                call_command('seed_demo', verbosity=0)  # running twice must not duplicate anything
        finally:
            shutil.rmtree(media, ignore_errors=True)
        self.assertEqual(Category.objects.count(), 6)
        self.assertEqual(Product.objects.count(), 24)
        self.assertTrue(Review.objects.exists())
