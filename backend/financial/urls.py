from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib import admin
from . import views

router = DefaultRouter()
router.register(r'invoices', views.InvoiceViewSet)
router.register(r'payments', views.PaymentViewSet)
router.register(r'revenues', views.RevenueViewSet)
router.register(r'client-balances', views.ClientBalanceViewSet)
router.register(r'company-revenues', views.CompanyRevenueViewSet)
router.register(r'dashboard/comprehensive', views.ComprehensiveDashboardViewSet, basename='comprehensive-dashboard')

urlpatterns = [
    path('dashboard/', views.financial_dashboard, name='financial_dashboard'),
    path('', include(router.urls)),
]