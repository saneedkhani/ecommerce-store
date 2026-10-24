from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter

from accounts.api_views import RegisterView, LoginView, LogoutView, MeView
from cart.api_views import CartView, CartItemViewSet
from orders.api_views import OrderViewSet
from payments.api_views import PaymentViewSet
from products.api_views import ProductViewSet

class PublicAPIRootView(DefaultRouter.APIRootView):
    """List of API endpoints (open to everyone, the endpoints themselves still check permissions)."""
    permission_classes = [AllowAny]


router = DefaultRouter()
router.APIRootView = PublicAPIRootView
router.register('products', ProductViewSet, basename='product')
router.register('cart/items', CartItemViewSet, basename='cart-item')
router.register('orders', OrderViewSet, basename='order')
router.register('payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/login/', LoginView.as_view(), name='api-login'),
    path('auth/logout/', LogoutView.as_view(), name='api-logout'),
    path('auth/me/', MeView.as_view(), name='api-me'),
    path('cart/', CartView.as_view(), name='api-cart'),

    # API documentation
    path('schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api-schema'), name='api-redoc'),

    path('', include(router.urls)),
]
