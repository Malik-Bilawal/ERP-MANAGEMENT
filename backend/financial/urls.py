from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'ledger', views.ClientLedgerViewSet, basename='client-ledger')
router.register(r'client-balances', views.ClientBalanceViewSet, basename='client-balance')
router.register(r'revenues', views.RevenueViewSet, basename='revenue')
router.register(r'company-revenues', views.CompanyRevenueViewSet, basename='company-revenue')
router.register(r'dashboard/comprehensive', views.ComprehensiveDashboardViewSet, basename='comprehensive-dashboard')

urlpatterns = [
    path('dashboard/', views.financial_dashboard, name='financial_dashboard'),
    path('', include(router.urls)),
]
