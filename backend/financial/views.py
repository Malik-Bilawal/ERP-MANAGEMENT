from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from decimal import Decimal
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Invoice, Revenue, ClientBalance, CompanyRevenue, Payment
from .serializers import (
    InvoiceSerializer, RevenueSerializer, ClientBalanceSerializer, CompanyRevenueSerializer,
    PaymentSerializer
)
from client_management.models import Client, Project
from hr.models import Employee, SalaryPayment, SalaryRecord
import csv


# ========== API VIEWSETS ==========

class InvoiceViewSet(viewsets.ModelViewSet):
    """Invoice API ViewSet"""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_id', 'client__name', 'project__name']
    ordering_fields = ['invoice_date', 'amount', 'created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by client
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter by project
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(invoice_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(invoice_date__lte=end_date)
        
        return queryset
    
    def perform_create(self, serializer):
        """Auto-set created_by when creating invoice"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Get detailed invoice information"""
        invoice = self.get_object()
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export invoices to CSV"""
        invoices = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="invoices_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Invoice ID', 'Invoice Number', 'Client', 'Project', 'Amount', 'Amount Paid', 'Status', 'Date', 'Notes'])
        
        for inv in invoices:
            writer.writerow([
                inv.invoice_id,
                inv.invoice_number,
                inv.client.name,
                inv.project.name,
                str(inv.amount),
                str(inv.amount_paid),
                inv.get_status_display(),
                inv.invoice_date.strftime('%Y-%m-%d'),
                inv.notes or ''
            ])
        
        return response
    
    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """Generate PDF invoice"""
        from django.template.loader import render_to_string
        import sys
        try:
            from xhtml2pdf import pisa
        except Exception:
            sys.exit(1)
        from io import BytesIO
        
        invoice = self.get_object()
        
        # Get payments for this invoice
        payments = invoice.payments.all()
        
        # Render HTML template
        context = {
            'invoice': invoice,
            'payments': payments,
            'company_name': 'ISM Company',
            'company_address': 'Your Company Address',
            'company_phone': 'Your Phone',
            'company_email': 'your@email.com',
        }
        
        html = render_to_string('admin/financial/invoice_pdf.html', context)
        
        # Create PDF
        buffer = BytesIO()
        pisa_status = pisa.CreatePDF(
            src=html,
            dest=buffer
        )
        
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
        return response


class PaymentViewSet(viewsets.ModelViewSet):
    """Payment API ViewSet - Record payments against invoices"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['payment_id', 'invoice__invoice_number', 'client__name']
    ordering_fields = ['payment_date', 'amount', 'created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by client
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter by invoice
        invoice_id = self.request.query_params.get('invoice')
        if invoice_id:
            queryset = queryset.filter(invoice_id=invoice_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
        
        return queryset
    
    def perform_create(self, serializer):
        """Auto-set created_by when creating payment"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export payments to CSV"""
        payments = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="payments_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Payment ID', 'Invoice', 'Client', 'Project', 'Amount', 'Method', 'Date', 'Reference', 'Notes'])
        
        for pay in payments:
            writer.writerow([
                pay.payment_id,
                pay.invoice.invoice_number,
                pay.client.name,
                pay.project.name,
                str(pay.amount),
                pay.get_payment_method_display(),
                pay.payment_date.strftime('%Y-%m-%d'),
                pay.transaction_reference or '',
                pay.notes or ''
            ])
        
        return response


class RevenueViewSet(viewsets.ReadOnlyModelViewSet):
    """Revenue API ViewSet - Read Only"""
    queryset = Revenue.objects.all()
    serializer_class = RevenueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['revenue_id', 'client__name', 'project__name']
    ordering_fields = ['revenue_date', 'amount']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by client
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(revenue_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(revenue_date__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get revenue summary"""
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        
        total_revenue = self.queryset.aggregate(total=Sum('amount'))['total'] or 0
        monthly_revenue = self.queryset.filter(
            revenue_date__gte=start_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'total_records': self.queryset.count()
        })


class ClientBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """Client Balance API ViewSet - Read Only"""
    queryset = ClientBalance.objects.all()
    serializer_class = ClientBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['client__name', 'client__email']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter clients with pending balance
        has_pending = self.request.query_params.get('has_pending')
        if has_pending and has_pending.lower() == 'true':
            queryset = queryset.filter(pending_balance__gt=0)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get client balance summary"""
        total_pending = self.queryset.aggregate(total=Sum('pending_balance'))['total'] or 0
        total_paid = self.queryset.aggregate(total=Sum('total_invoiced'))['total'] or 0
        total_cost = self.queryset.aggregate(total=Sum('total_projects_cost'))['total'] or 0
        
        return Response({
            'total_pending': total_pending,
            'total_paid': total_paid,
            'total_projects_cost': total_cost,
            'total_clients_with_balance': self.queryset.filter(pending_balance__gt=0).count()
        })


class CompanyRevenueViewSet(viewsets.ReadOnlyModelViewSet):
    """Company Revenue API ViewSet - Read Only"""
    queryset = CompanyRevenue.objects.all()
    serializer_class = CompanyRevenueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date', 'total_revenue']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current day's revenue"""
        today = timezone.now().date()
        revenue, created = CompanyRevenue.objects.get_or_create(
            date=today,
            defaults={
                'total_revenue': 0,
                'total_clients': Client.objects.filter(status='active').count(),
                'total_projects': Project.objects.count(),
                'active_projects': Project.objects.filter(status='in_progress').count(),
            }
        )
        serializer = self.get_serializer(revenue)
        return Response(serializer.data)


# ========== DASHBOARD VIEW ==========

@staff_member_required
def financial_dashboard(request):
    """Professional Financial Dashboard"""
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
    
    # Total Revenue
    total_revenue = Revenue.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Current Month Revenue
    current_month_revenue = Revenue.objects.filter(
        revenue_date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Last Month Revenue
    last_month_revenue = Revenue.objects.filter(
        revenue_date__gte=last_month_start,
        revenue_date__lt=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Calculate growth
    if last_month_revenue > 0:
        monthly_growth = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100
    else:
        monthly_growth = 100 if current_month_revenue > 0 else 0
    
    # Pending Payments
    pending_payments = ClientBalance.objects.aggregate(total=Sum('pending_balance'))['total'] or Decimal('0.00')
    
    # Clients Stats
    total_clients = Client.objects.filter(status='active').count()
    new_clients = Client.objects.filter(
        created_at__gte=start_of_month
    ).count()
    
    # Projects Stats
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(status='in_progress').count()
    completed_projects = Project.objects.filter(status='completed').count()
    
    # Net Profit (Revenue - Expenses - but we don't have expenses yet)
    net_profit = total_revenue  # Simplified for now
    profit_margin = 100 if total_revenue > 0 else 0
    
    # Monthly Revenue Data for Chart (last 6 months)
    monthly_data = []
    monthly_labels = []
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if i == 0:
            month_end = today
        else:
            next_month = month_date.replace(day=28) + timedelta(days=4)
            month_end = next_month - timedelta(days=next_month.day)
        
        monthly_revenue = Revenue.objects.filter(
            revenue_date__gte=month_start,
            revenue_date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        monthly_data.append(float(monthly_revenue))
        monthly_labels.append(month_start.strftime('%b %Y'))
    
    # Top Clients
    top_clients = []
    client_balances = ClientBalance.objects.select_related('client').all()
    
    for cb in client_balances.order_by('-total_invoiced')[:5]:
        payment_percentage = (cb.total_invoiced / cb.total_projects_cost * 100) if cb.total_projects_cost > 0 else 0
        top_clients.append({
            'name': cb.client.name,
            'total_cost': cb.total_projects_cost,
            'total_paid': cb.total_invoiced,
            'pending': cb.pending_balance,
            'payment_percentage': payment_percentage
        })
    
    # Top Client Names for Chart
    top_client_names = [c['name'] for c in top_clients[:5]]
    top_client_payments = [float(c['total_paid']) for c in top_clients[:5]]
    
    # Project Status Distribution
    project_statuses = Project.objects.values('status').annotate(count=Count('status'))
    project_status_labels = []
    project_status_counts = []
    
    status_map = {
        'planning': 'Planning',
        'in_progress': 'In Progress',
        'completed': 'Completed',
        'on_hold': 'On Hold',
        'cancelled': 'Cancelled'
    }
    
    for status in project_statuses:
        project_status_labels.append(status_map.get(status['status'], status['status']))
        project_status_counts.append(status['count'])
    
    # Recent Invoices
    recent_invoices = Invoice.objects.select_related('client', 'project').all()[:10]
    
    # Total salary expenses (all salary payments - both pending and completed)
    from hr.models import Employee, SalaryPayment as HRSalaryPayment
    total_employees = Employee.objects.filter(is_active=True).count()
    total_salary_expenses = HRSalaryPayment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Use existing total_revenue that's already calculated above (line 322)
    # total_revenue is already defined - just use it
    
    context = {
        'title': 'Financial Dashboard',
        'total_revenue': total_revenue,
        'current_month_revenue': current_month_revenue,
        'monthly_growth': round(monthly_growth, 1),
        'pending_payments': pending_payments,
        'pending_trend': 0,
        'total_clients': total_clients,
        'new_clients': new_clients,
        'active_projects': active_projects,
        'total_projects': total_projects,
        'net_profit': net_profit,
        'profit_margin': round(profit_margin, 1),
        'total_employees': total_employees,
        'total_salary_expenses': total_salary_expenses,
        'monthly_labels': monthly_labels,
        'monthly_revenue': monthly_data,
        'top_client_names': top_client_names,
        'top_client_payments': top_client_payments,
        'top_clients': top_clients,
        'project_status_labels': project_status_labels,
        'project_status_counts': project_status_counts,
        'recent_invoices': recent_invoices,
    }
    
    return render(request, 'admin/financial/dashboard.html', context)


# ========== DASHBOARD API VIEWSET (Alternative API endpoint) ==========

class DashboardViewSet(viewsets.ViewSet):
    """Dashboard API ViewSet"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get quick dashboard statistics"""
        total_revenue = Revenue.objects.aggregate(total=Sum('amount'))['total'] or 0
        pending_payments = ClientBalance.objects.aggregate(total=Sum('pending_balance'))['total'] or 0
        total_clients = Client.objects.filter(status='active').count()
        active_projects = Project.objects.filter(status='in_progress').count()
        
        return Response({
            'total_revenue': total_revenue,
            'pending_payments': pending_payments,
            'total_clients': total_clients,
            'active_projects': active_projects
        })
    
    @action(detail=False, methods=['get'])
    def monthly_trend(self, request):
        """Get monthly revenue trend"""
        today = timezone.now().date()
        monthly_data = []
        
        for i in range(5, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            if i == 0:
                month_end = today
            else:
                next_month = month_date.replace(day=28) + timedelta(days=4)
                month_end = next_month - timedelta(days=next_month.day)
            
            monthly_revenue = Revenue.objects.filter(
                revenue_date__gte=month_start,
                revenue_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_data.append({
                'month': month_start.strftime('%B %Y'),
                'revenue': monthly_revenue
            })
        
        return Response(monthly_data)


# ========== COMPREHENSIVE DASHBOARD API ==========

class ComprehensiveDashboardViewSet(viewsets.ViewSet):
    """Complete Dashboard API - Income, Expenses, Revenue all in one place"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get complete financial summary"""
        from django.db.models import Q
        
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        current_year = today.year
        
        # ========== INCOME DATA ==========
        # Total Revenue (all time)
        total_revenue = Revenue.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Revenue this month
        revenue_this_month = Revenue.objects.filter(
            revenue_date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Revenue this year
        revenue_this_year = Revenue.objects.filter(
            revenue_date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Total Pending Payments
        total_pending = Invoice.objects.filter(
            status__in=['unpaid', 'partial']
        ).aggregate(total=Sum('remaining_amount'))['total'] or Decimal('0.00')
        
        # ========== CLIENT & PROJECT STATS ==========
        total_clients = Client.objects.count()
        active_projects = Project.objects.filter(status='in_progress').count()
        total_projects = Project.objects.count()
        
        # ========== EXPENSE DATA (Salary/Employee Costs) ==========
        # Total salary paid all time
        total_salary_paid = SalaryPayment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Salary this month
        salary_this_month = SalaryPayment.objects.filter(
            status='completed',
            payment_date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Salary this year
        salary_this_year = SalaryPayment.objects.filter(
            status='completed',
            payment_date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Pending salary
        pending_salary = SalaryPayment.objects.filter(
            status='pending'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Total employees
        total_employees = Employee.objects.filter(is_active=True).count()
        
        # ========== PAYMENT LOGS ==========
        # Recent client payments (income)
        recent_client_payments = Payment.objects.select_related(
            'client', 'project', 'invoice'
        ).order_by('-payment_date')[:10]
        
        # Recent salary payments (expense)
        recent_salary_payments = SalaryPayment.objects.select_related(
            'employee'
        ).order_by('-payment_date')[:10]
        
        # Recent invoices
        recent_invoices = Invoice.objects.select_related(
            'client', 'project'
        ).order_by('-created_at')[:10]
        
        return Response({
            # Income Summary
            'total_revenue': float(total_revenue),
            'revenue_this_month': float(revenue_this_month),
            'revenue_this_year': float(revenue_this_year),
            'total_pending': float(total_pending),
            
            # Business Stats
            'total_clients': total_clients,
            'active_projects': active_projects,
            'total_projects': total_projects,
            
            # Expense (Salary) Summary
            'total_salary_paid': float(total_salary_paid),
            'salary_this_month': float(salary_this_month),
            'salary_this_year': float(salary_this_year),
            'pending_salary': float(pending_salary),
            'total_employees': total_employees,
            
            # Net Income
            'net_income_all_time': float(total_revenue - total_salary_paid),
            'net_income_this_month': float(revenue_this_month - salary_this_month),
            'net_income_this_year': float(revenue_this_year - salary_this_year),
        })
    
    @action(detail=False, methods=['get'])
    def recent_payments(self, request):
        """Get all recent payment logs (income + expenses)"""
        # Client payments (Income)
        client_payments = Payment.objects.select_related(
            'client', 'project', 'invoice'
        ).order_by('-payment_date')[:50]
        
        # Salary payments (Expense)
        salary_payments = SalaryPayment.objects.select_related(
            'employee'
        ).order_by('-payment_date')[:50]
        
        # Combine and format
        income_logs = []
        for payment in client_payments:
            income_logs.append({
                'id': payment.id,
                'type': 'client_payment',
                'payment_id': payment.payment_id,
                'description': f"Payment from {payment.client.name} - {payment.project.name}",
                'amount': float(payment.amount),
                'date': payment.payment_date.isoformat(),
                'status': payment.status,
                'method': payment.payment_method,
                'reference': payment.transaction_reference,
            })
        
        expense_logs = []
        for payment in salary_payments:
            expense_logs.append({
                'id': payment.id,
                'type': 'salary_payment',
                'payment_id': payment.payment_id,
                'description': f"Salary for {payment.employee.full_name} - {payment.month.strftime('%B %Y')}",
                'amount': float(payment.amount),
                'date': payment.payment_date.isoformat() if payment.payment_date else None,
                'status': payment.status,
                'method': payment.payment_method,
                'reference': payment.transaction_reference,
            })
        
        return Response({
            'income': income_logs,
            'expense': expense_logs,
        })
    
    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly revenue vs expense comparison"""
        from datetime import datetime
        
        today = timezone.now().date()
        monthly_data = []
        
        # Last 12 months
        for i in range(11, -1, -1):
            if i >= today.month:
                continue
            
            month_date = today.replace(month=today.month - i) if today.month > i else today.replace(month=today.month - i + 12, year=today.year - 1)
            month_start = month_date.replace(day=1)
            
            if month_date.month == today.month and month_date.year == today.year:
                month_end = today
            else:
                next_month = month_start.replace(day=28) + timedelta(days=4)
                month_end = (next_month - timedelta(days=next_month.day))
            
            # Revenue this month
            revenue = Revenue.objects.filter(
                revenue_date__gte=month_start,
                revenue_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Salary this month
            salary = SalaryPayment.objects.filter(
                status='completed',
                payment_date__gte=month_start,
                payment_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'revenue': float(revenue),
                'salary_expense': float(salary),
                'net_income': float(revenue - salary),
            })
        
        return Response(monthly_data)