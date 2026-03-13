# salary/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# Change this line from 'SalaryViewSet' to 'SalarySlipViewSet'
# router.register(r'salaries', views.SalaryViewSet, basename='salary')  # OLD - WRONG
router.register(r'salary-structures', views.SalaryStructureViewSet, basename='salarystructure')
router.register(r'salary-assignments', views.SalaryAssignmentViewSet, basename='salaryassignment')
router.register(r'salary-slips', views.SalarySlipViewSet, basename='salaryslip')
router.register(r'invoices', views.StaffInvoiceViewSet, basename='staffinvoice')
router.register(r'invoice-items', views.InvoiceLineItemViewSet, basename='invoicelineitem')

urlpatterns = [
    path('api/', include(router.urls)),
]