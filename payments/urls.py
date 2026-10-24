from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('submit/<int:order_id>/', views.submit_payment, name='submit_payment'),
    path('submitted/<int:order_id>/', views.payment_submitted, name='payment_submitted'),
    path('dashboard/', views.payment_dashboard, name='dashboard'),
    path('pending-count/', views.pending_count, name='pending_count'),
    path('update/<int:payment_id>/<str:new_status>/', views.update_payment_status, name='update_status'),
]