from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')

urlpatterns = [
    path('', include(router.urls)),
]