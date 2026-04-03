from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeRoleViewSet,
    EmployeeViewSet,
    SalaryRecordViewSet,
    SalaryPaymentViewSet,
    MonthlyExpensePlanViewSet,
    ExpenseCategoryViewSet,
    ActualExpenseViewSet,
    HRDashboardViewSet,
)

router = DefaultRouter()
router.register(r'roles', EmployeeRoleViewSet, basename='employee-role')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'salary-records', SalaryRecordViewSet, basename='salary-record')
router.register(r'salary-payments', SalaryPaymentViewSet, basename='salary-payment')
router.register(r'expense-plans', MonthlyExpensePlanViewSet, basename='expense-plan')
router.register(r'expense-categories', ExpenseCategoryViewSet, basename='expense-category')
router.register(r'expenses', ActualExpenseViewSet, basename='actual-expense')
router.register(r'dashboard', HRDashboardViewSet, basename='hr-dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
