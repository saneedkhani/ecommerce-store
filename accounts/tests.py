from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

User = get_user_model()


class AuthApiTests(APITestCase):
    def test_register_returns_token(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'alice', 'email': 'alice@example.test', 'password': 'Strong-pass-123'})
        self.assertEqual(response.status_code, 201)
        self.assertIn('token', response.data)
        self.assertTrue(User.objects.filter(username='alice').exists())

    def test_register_rejects_weak_password(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'bob', 'email': 'bob@example.test', 'password': '123'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.data)

    def test_login_me_and_logout(self):
        User.objects.create_user('carol', password='Strong-pass-123')
        response = self.client.post('/api/auth/login/', {'username': 'carol', 'password': 'Strong-pass-123'})
        self.assertEqual(response.status_code, 200)
        token = response.data['token']

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(self.client.get('/api/auth/me/').data['username'], 'carol')

        self.assertEqual(self.client.post('/api/auth/logout/').status_code, 204)
        self.assertFalse(Token.objects.filter(key=token).exists())

    def test_login_wrong_password(self):
        User.objects.create_user('dave', password='Strong-pass-123')
        response = self.client.post('/api/auth/login/', {'username': 'dave', 'password': 'wrong'})
        self.assertEqual(response.status_code, 400)

    def test_me_requires_login(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)
