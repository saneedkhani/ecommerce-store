from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/orders/', views.staff_orders, name='staff_orders'),
    path('dashboard/orders/<int:order_id>/status/', views.staff_update_order, name='staff_update_order'),
    path('dashboard/products/', views.staff_products, name='staff_products'),
]
