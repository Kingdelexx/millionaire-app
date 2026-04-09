from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('donate/', views.donate_view, name='donate'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('paystack/callback/', views.paystack_callback, name='paystack_callback'),
    path('toggle-auto-enter/', views.toggle_auto_enter, name='toggle_auto_enter'),
]
