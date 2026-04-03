import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    EmployeeRole, Employee, SalaryRecord, SalaryPayment,
    MonthlyExpensePlan, ExpenseCategory, ActualExpense
)
from .serializers import (
    EmployeeRoleSerializer,
    EmployeeSerializer, EmployeeListSerializer, EmployeeDetailSerializer,
    SalaryRecordSerializer, SalaryRecordListSerializer,
    SalaryPaymentSerializer, SalaryPaymentListSerializer,
    MonthlyExpensePlanSerializer, MonthlyExpensePlanListSerializer,
    ExpenseCategorySerializer,
    ActualExpenseSerializer, ActualExpenseListSerializer,
    SalaryGenerateSerializer, SalaryBulkProcessSerializer,
    MonthlyPlanAutoCalculateSerializer
)

logger = logging.getLogger(__name__)


class EmployeeRoleViewSet(viewsets.ModelViewSet):
    """CRUD for employee roles"""
    queryset = EmployeeRole.objects.all()
    serializer_class = EmployeeRoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['role_name', 'description']
    ordering_fields = ['role_name', 'created_at']
    ordering = ['role_name']


class EmployeeViewSet(viewsets.ModelViewSet):
    """CRUD for employees with salary management"""
    queryset = Employee.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'employee_id']
    ordering_fields = ['created_at', 'first_name', 'salary', 'joining_date']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        elif self.action == 'retrieve':
            return EmployeeDetailSerializer
        return EmployeeSerializer
    
    def get_queryset(self):
        queryset = Employee.objects.select_related('role').all()
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        employment_type = self.request.query_params.get('employment_type')
        if employment_type:
            queryset = queryset.filter(employment_type=employment_type)
        
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role_id=role)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['get'])
    def salary_history(self, request, pk=None):
        """Get complete salary history for an employee"""
        employee = self.get_object()
        records = employee.salary_records.all().order_by('-month')
        serializer = SalaryRecordSerializer(records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def payment_history(self, request, pk=None):
        """Get payment history for an employee"""
        employee = self.get_object()
        payments = employee.salary_payments.all().order_by('-month')
        serializer = SalaryPaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def salary_summary(self, request, pk=None):
        """Get salary summary for an employee"""
        employee = self.get_object()
        year = request.query_params.get('year', timezone.now().year)
        summary = employee.get_salary_summary(year=int(year))
        return Response(summary)
    
    @action(detail=True, methods=['get'])
    def unpaid_months(self, request, pk=None):
        """Get list of unpaid months for an employee"""
        employee = self.get_object()
        unpaid = employee.get_unpaid_months()
        serializer = SalaryRecordSerializer(unpaid, many=True)
        return Response(serializer.data)


class SalaryRecordViewSet(viewsets.ModelViewSet):
    """CRUD for salary records"""
    queryset = SalaryRecord.objects.select_related('employee').all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']
    ordering_fields = ['month', 'net_salary', 'is_paid']
    ordering = ['-month']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SalaryRecordListSerializer
        return SalaryRecordSerializer
    
    def get_queryset(self):
        queryset = SalaryRecord.objects.select_related('employee').all()
        
        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(month=month)
        
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(month__year=year)
        
        is_paid = self.request.query_params.get('is_paid')
        if is_paid is not None:
            queryset = queryset.filter(is_paid=is_paid.lower() == 'true')
        
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=False, methods=['post'])
    def generate_monthly(self, request):
        """Auto-generate salary records for all active employees for a given month"""
        serializer = SalaryGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        month = serializer.validated_data['month']
        include_inactive = serializer.validated_data.get('include_inactive', False)
        
        employees = Employee.objects.filter(is_active=True) if not include_inactive else Employee.objects.all()
        
        created = 0
        skipped = 0
        records = []
        
        for employee in employees:
            record, record_created = SalaryRecord.objects.get_or_create(
                employee=employee,
                month=month,
                defaults={
                    'base_salary': employee.salary,
                    'bonus': Decimal('0.00'),
                    'deductions': Decimal('0.00'),
                }
            )
            
            if record_created:
                created += 1
                records.append(record)
            else:
                skipped += 1
        
        return Response({
            'month': month.strftime('%B %Y'),
            'created': created,
            'skipped': skipped,
            'total_employees': employees.count(),
            'records': SalaryRecordSerializer(records, many=True).data if records else []
        }, status=status.HTTP_201_CREATED if created > 0 else status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get salary records summary for a month/year"""
        month = request.query_params.get('month')
        year = request.query_params.get('year', timezone.now().year)
        
        queryset = self.get_queryset().filter(month__year=year)
        if month:
            queryset = queryset.filter(month=month)
        
        total_earned = queryset.aggregate(total=Sum('net_salary'))['total'] or Decimal('0.00')
        total_paid = queryset.filter(is_paid=True).aggregate(total=Sum('net_salary'))['total'] or Decimal('0.00')
        total_pending = queryset.filter(is_paid=False).aggregate(total=Sum('net_salary'))['total'] or Decimal('0.00')
        
        return Response({
            'period': month or f'Year {year}',
            'total_records': queryset.count(),
            'paid_records': queryset.filter(is_paid=True).count(),
            'unpaid_records': queryset.filter(is_paid=False).count(),
            'total_earned': total_earned,
            'total_paid': total_paid,
            'total_pending': total_pending,
        })


class SalaryPaymentViewSet(viewsets.ModelViewSet):
    """CRUD for salary payments"""
    queryset = SalaryPayment.objects.select_related('employee', 'created_by').all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id', 'payment_id']
    ordering_fields = ['month', 'amount', 'payment_date', 'status']
    ordering = ['-month', '-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SalaryPaymentListSerializer
        return SalaryPaymentSerializer
    
    def get_queryset(self):
        queryset = SalaryPayment.objects.select_related('employee', 'created_by').all()
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(month=month)
        
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(month__year=year)
        
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def bulk_process(self, request):
        """Bulk process salary payments (change status for multiple payments)"""
        serializer = SalaryBulkProcessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment_ids = serializer.validated_data['payment_ids']
        new_status = serializer.validated_data['new_status']
        payment_method = serializer.validated_data.get('payment_method')
        payment_date = serializer.validated_data.get('payment_date')
        
        payments = SalaryPayment.objects.filter(id__in=payment_ids)
        updated_count = 0
        
        for payment in payments:
            payment.status = new_status
            if payment_method:
                payment.payment_method = payment_method
            if payment_date:
                payment.payment_date = payment_date
            payment.save()
            updated_count += 1
        
        return Response({
            'updated': updated_count,
            'new_status': new_status,
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get salary payment summary"""
        year = request.query_params.get('year', timezone.now().year)
        month = request.query_params.get('month')
        
        queryset = self.get_queryset().filter(month__year=year)
        if month:
            queryset = queryset.filter(month=month)
        
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        completed_amount = queryset.filter(status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        pending_amount = queryset.filter(status='pending').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return Response({
            'period': month or f'Year {year}',
            'total_payments': queryset.count(),
            'completed_payments': queryset.filter(status='completed').count(),
            'pending_payments': queryset.filter(status='pending').count(),
            'total_amount': total_amount,
            'completed_amount': completed_amount,
            'pending_amount': pending_amount,
        })
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending salary payments"""
        pending = self.get_queryset().filter(status='pending').order_by('month')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)


class MonthlyExpensePlanViewSet(viewsets.ModelViewSet):
    """CRUD for monthly expense plans"""
    queryset = MonthlyExpensePlan.objects.select_related('created_by').all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['month', 'total_planned', 'status']
    ordering = ['-month']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MonthlyExpensePlanListSerializer
        return MonthlyExpensePlanSerializer
    
    def get_queryset(self):
        queryset = MonthlyExpensePlan.objects.select_related('created_by').all()
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(month__year=year)
        
        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(month=month)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def auto_calculate(self, request):
        """Auto-calculate planned salary from active employees for a given month"""
        serializer = MonthlyPlanAutoCalculateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        month = serializer.validated_data['month']
        
        plan, created = MonthlyExpensePlan.objects.get_or_create(
            month=month,
            defaults={'created_by': request.user}
        )
        
        total_salary = plan.auto_calculate_salary()
        plan.save()
        
        return Response({
            'plan_id': plan.plan_id,
            'month': month.strftime('%B %Y'),
            'auto_calculated_salary': total_salary,
            'total_planned': plan.total_planned,
            'created': created,
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an expense plan"""
        plan = self.get_object()
        if plan.status not in ['draft', 'planned']:
            return Response(
                {'error': 'Only draft or planned plans can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        plan.status = 'approved'
        plan.save()
        return Response({'status': 'approved', 'plan_id': plan.plan_id})
    
    @action(detail=True, methods=['post'])
    def generate_salary_payments(self, request, pk=None):
        """Generate salary payments for all employees from an approved plan"""
        plan = self.get_object()
        
        if plan.status != 'approved':
            return Response(
                {'error': 'Plan must be approved before generating payments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan_month = plan.month
        active_employees = Employee.objects.filter(is_active=True)
        
        created = 0
        skipped = 0
        
        for employee in active_employees:
            payment, payment_created = SalaryPayment.objects.get_or_create(
                employee=employee,
                month=plan_month,
                defaults={
                    'amount': employee.salary,
                    'status': 'pending',
                    'created_by': request.user,
                }
            )
            
            if payment_created:
                created += 1
            else:
                skipped += 1
        
        plan.status = 'processing'
        plan.save()
        
        return Response({
            'plan_id': plan.plan_id,
            'payments_created': created,
            'payments_skipped': skipped,
            'plan_status': 'processing',
        })
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        """Mark a plan as complete after all payments are done"""
        plan = self.get_object()
        
        if plan.status != 'processing':
            return Response(
                {'error': 'Plan must be in processing state to mark complete'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan.status = 'completed'
        plan.save()
        
        return Response({
            'plan_id': plan.plan_id,
            'status': 'completed',
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get expense plans summary"""
        year = request.query_params.get('year', timezone.now().year)
        
        plans = self.get_queryset().filter(month__year=year)
        
        total_planned = plans.aggregate(total=Sum('total_planned'))['total'] or Decimal('0.00')
        
        return Response({
            'year': year,
            'total_plans': plans.count(),
            'total_planned': total_planned,
            'by_status': {
                'draft': plans.filter(status='draft').count(),
                'planned': plans.filter(status='planned').count(),
                'approved': plans.filter(status='approved').count(),
                'processing': plans.filter(status='processing').count(),
                'completed': plans.filter(status='completed').count(),
                'cancelled': plans.filter(status='cancelled').count(),
            }
        })


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """CRUD for expense categories"""
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'expense_type']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = ExpenseCategory.objects.all()
        
        expense_type = self.request.query_params.get('expense_type')
        if expense_type:
            queryset = queryset.filter(expense_type=expense_type)
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


class ActualExpenseViewSet(viewsets.ModelViewSet):
    """CRUD for actual expenses tracking"""
    queryset = ActualExpense.objects.select_related('category', 'employee', 'created_by').all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'expense_id', 'employee__first_name', 'employee__last_name']
    ordering_fields = ['expense_date', 'amount', 'status']
    ordering = ['-expense_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ActualExpenseListSerializer
        return ActualExpenseSerializer
    
    def get_queryset(self):
        queryset = ActualExpense.objects.select_related('category', 'employee', 'created_by').all()
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        expense_type = self.request.query_params.get('expense_type')
        if expense_type:
            queryset = queryset.filter(category__expense_type=expense_type)
        
        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(expense_month=month)
        
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(expense_month__year=year)
        
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an expense"""
        expense = self.get_object()
        if expense.status != 'pending':
            return Response(
                {'error': 'Only pending expenses can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        expense.status = 'approved'
        expense.save()
        return Response({'status': 'approved', 'expense_id': expense.expense_id})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark an expense as completed"""
        expense = self.get_object()
        if expense.status not in ['pending', 'approved']:
            return Response(
                {'error': 'Only pending or approved expenses can be marked complete'},
                status=status.HTTP_400_BAD_REQUEST
            )
        expense.status = 'completed'
        expense.save()
        return Response({'status': 'completed', 'expense_id': expense.expense_id})
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get expenses summary"""
        year = request.query_params.get('year', timezone.now().year)
        month = request.query_params.get('month')
        
        queryset = self.get_queryset().filter(expense_month__year=year)
        if month:
            queryset = queryset.filter(expense_month=month)
        
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        completed_amount = queryset.filter(status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        pending_amount = queryset.filter(status='pending').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        by_type = {}
        for expense_type in dict(ExpenseCategory.EXPENSE_TYPES).keys():
            type_total = queryset.filter(
                category__expense_type=expense_type
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            by_type[expense_type] = type_total
        
        return Response({
            'period': month or f'Year {year}',
            'total_expenses': queryset.count(),
            'total_amount': total_amount,
            'completed_amount': completed_amount,
            'pending_amount': pending_amount,
            'by_type': by_type,
        })


class HRDashboardViewSet(viewsets.ViewSet):
    """HR Dashboard with aggregated statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get complete HR and salary overview"""
        now = timezone.now()
        current_month = now.replace(day=1)
        
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(is_active=True).count()
        inactive_employees = total_employees - active_employees
        
        monthly_salary = Employee.objects.filter(is_active=True).aggregate(
            total=Sum('salary')
        )['total'] or Decimal('0.00')
        
        current_records = SalaryRecord.objects.filter(month=current_month)
        current_paid = current_records.filter(is_paid=True)
        current_unpaid = current_records.filter(is_paid=False)
        
        current_payments = SalaryPayment.objects.filter(month=current_month)
        completed_payments = current_payments.filter(status='completed')
        pending_payments = current_payments.filter(status='pending')
        
        current_plan = MonthlyExpensePlan.objects.filter(month=current_month).first()
        
        year_payments = SalaryPayment.objects.filter(
            month__year=now.year,
            status='completed'
        )
        year_total_paid = year_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        current_actual_expenses = ActualExpense.objects.filter(
            expense_month=current_month,
            status='completed'
        )
        current_expenses_total = current_actual_expenses.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        return Response({
            'employees': {
                'total': total_employees,
                'active': active_employees,
                'inactive': inactive_employees,
                'monthly_salary_budget': monthly_salary,
            },
            'current_month': {
                'month': current_month.strftime('%B %Y'),
                'salary_records': {
                    'total': current_records.count(),
                    'paid': current_paid.count(),
                    'unpaid': current_unpaid.count(),
                },
                'payments': {
                    'total': current_payments.count(),
                    'completed': completed_payments.count(),
                    'pending': pending_payments.count(),
                    'completed_amount': completed_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
                },
                'actual_expenses': current_expenses_total,
            },
            'year_summary': {
                'year': now.year,
                'total_salary_paid': year_total_paid,
            },
            'current_plan': {
                'exists': current_plan is not None,
                'plan_id': current_plan.plan_id if current_plan else None,
                'status': current_plan.status if current_plan else None,
                'total_planned': float(current_plan.total_planned) if current_plan else None,
            } if current_plan else None,
        })
    
    @action(detail=False, methods=['get'])
    def monthly_trend(self, request):
        """Get monthly salary expense trend for last 12 months"""
        months = []
        now = timezone.now()
        
        for i in range(11, -1, -1):
            month_date = now - timedelta(days=30 * i)
            month_start = month_date.replace(day=1)
            
            payments = SalaryPayment.objects.filter(
                month=month_start,
                status='completed'
            )
            total_paid = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            expenses = ActualExpense.objects.filter(
                expense_month=month_start,
                status='completed'
            )
            total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            months.append({
                'month': month_start.strftime('%B %Y'),
                'salary_paid': total_paid,
                'other_expenses': total_expenses,
                'total': total_paid + total_expenses,
            })
        
        return Response(months)
    
    @action(detail=False, methods=['get'])
    def pending_actions(self, request):
        """Get list of pending HR actions"""
        pending_payments = SalaryPayment.objects.filter(status='pending').count()
        unpaid_records = SalaryRecord.objects.filter(is_paid=False).count()
        pending_expenses = ActualExpense.objects.filter(status='pending').count()
        draft_plans = MonthlyExpensePlan.objects.filter(status='draft').count()
        
        return Response({
            'pending_salary_payments': pending_payments,
            'unpaid_salary_records': unpaid_records,
            'pending_expenses': pending_expenses,
            'draft_expense_plans': draft_plans,
            'total_pending': pending_payments + unpaid_records + pending_expenses + draft_plans,
        })
