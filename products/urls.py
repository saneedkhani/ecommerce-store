from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='category'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:pk>/review/', views.add_review, name='add_review'),
    path('<int:pk>/wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add/', views.add_or_restock_product, name='add_product'),
    path('<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('<int:pk>/delete/', views.delete_product, name='delete_product'),
]
