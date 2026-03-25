from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'invoices', views.InvoiceViewSet)
router.register(r'revenues', views.RevenueViewSet)
router.register(r'client-balances', views.ClientBalanceViewSet)
router.register(r'company-revenues', views.CompanyRevenueViewSet)
router.register(r'dashboard', views.DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]