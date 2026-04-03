from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from decimal import Decimal
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Invoice, InvoiceItem, Payment, ClientLedger, ClientBalance, Revenue, CompanyRevenue
from .serializers import (
    InvoiceSerializer, InvoiceCreateSerializer, PaymentSerializer,
    ClientLedgerSerializer, ClientLedgerDetailSerializer, ClientBalanceSerializer,
    RevenueSerializer, CompanyRevenueSerializer
)
from client_management.models import Client, Project
from hr.models import Employee, SalaryPayment, SalaryRecord
import csv


class InvoiceViewSet(viewsets.ModelViewSet):
    """Invoice API ViewSet"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_id', 'invoice_number', 'client__name', 'project__name']
    ordering_fields = ['invoice_date', 'amount', 'created_at']

    def get_queryset(self):
        queryset = Invoice.objects.select_related('client', 'project').prefetch_related('items', 'payments').all()

        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)

        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(invoice_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(invoice_date__lte=end_date)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer
        return InvoiceSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def project_details(self, request):
        """Get project details with remaining budget for invoice creation."""
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({'error': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'id': project.id,
            'project_id': project.project_id,
            'name': project.name,
            'budget': str(project.budget),
            'total_invoiced': str(project.total_invoiced),
            'remaining_budget': str(project.remaining_budget),
        })

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        invoice = self.get_object()
        serializer = self.get_serializer(invoice)
        payments = Payment.objects.filter(invoice=invoice).order_by('-payment_date')
        return Response({
            'invoice': serializer.data,
            'payments': PaymentSerializer(payments, many=True).data,
        })

    @action(detail=False, methods=['get'])
    def export(self, request):
        invoices = self.get_queryset()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="invoices_{timezone.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Invoice ID', 'Invoice Number', 'Client', 'Project', 'Amount', 'Amount Paid', 'Remaining', 'Status', 'Date', 'Notes'])

        for inv in invoices:
            remaining = float(inv.amount) - float(inv.amount_paid)
            writer.writerow([
                inv.invoice_id,
                inv.invoice_number,
                inv.client.name if inv.client else 'N/A',
                inv.project.name if inv.project else 'N/A',
                str(inv.amount),
                str(inv.amount_paid),
                f"{remaining:.2f}",
                inv.get_status_display(),
                inv.invoice_date.strftime('%Y-%m-%d') if inv.invoice_date else '',
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
        payments = invoice.payments.all()

        context = {
            'invoice': invoice,
            'payments': payments,
            'company_name': 'ISM Company',
            'company_address': 'Your Company Address',
            'company_phone': 'Your Phone',
            'company_email': 'your@email.com',
        }

        html = render_to_string('admin/financial/invoice_pdf.html', context)

        buffer = BytesIO()
        pisa_status = pisa.CreatePDF(src=html, dest=buffer)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
        return response


class PaymentViewSet(viewsets.ModelViewSet):
    """Payment API ViewSet - Record payments against invoices"""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['payment_id', 'invoice__invoice_number', 'client__name']
    ordering_fields = ['payment_date', 'amount', 'created_at']

    def get_queryset(self):
        queryset = Payment.objects.select_related('client', 'project', 'invoice').all()

        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)

        invoice_id = self.request.query_params.get('invoice')
        if invoice_id:
            queryset = queryset.filter(invoice_id=invoice_id)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)

        return queryset

    def perform_create(self, serializer):
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
                pay.client.name if pay.client else 'N/A',
                pay.project.name if pay.project else 'N/A',
                str(pay.amount),
                pay.get_payment_method_display(),
                pay.payment_date.strftime('%Y-%m-%d') if pay.payment_date else '',
                pay.transaction_reference or '',
                pay.notes or ''
            ])

        return response


class ClientLedgerViewSet(viewsets.ReadOnlyModelViewSet):
    """Client Ledger API - per-client transaction history"""
    serializer_class = ClientLedgerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['client__name', 'description']
    ordering_fields = ['transaction_date', 'created_at']

    def get_queryset(self):
        queryset = ClientLedger.objects.select_related('client', 'project', 'invoice', 'payment').all()

        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)

        transaction_type = self.request.query_params.get('type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(transaction_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(transaction_date__lte=end_date)

        return queryset

    @action(detail=False, methods=['get'])
    def by_client(self, request):
        """Get full ledger detail for a specific client"""
        client_id = request.query_params.get('client_id')
        if not client_id:
            return Response({'error': 'client_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client.objects.get(pk=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

        balance, _ = ClientBalance.objects.get_or_create(client=client)
        serializer = ClientLedgerDetailSerializer(balance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get ledger summary across all clients"""
        total_invoiced = ClientLedger.objects.filter(transaction_type='invoice').aggregate(total=Sum('debit'))['total'] or Decimal('0.00')
        total_paid = ClientLedger.objects.filter(transaction_type='payment').aggregate(total=Sum('credit'))['total'] or Decimal('0.00')

        return Response({
            'total_invoiced': float(total_invoiced),
            'total_paid': float(total_paid),
            'total_pending': float(total_invoiced - total_paid),
            'total_entries': ClientLedger.objects.count(),
        })


class ClientBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """Client Balance API ViewSet - Read Only"""
    queryset = ClientBalance.objects.select_related('client').all()
    serializer_class = ClientBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['client__name', 'client__email']

    def get_queryset(self):
        queryset = super().get_queryset()

        has_pending = self.request.query_params.get('has_pending')
        if has_pending and has_pending.lower() == 'true':
            queryset = queryset.filter(pending_balance__gt=0)

        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get client balance summary"""
        total_pending = self.queryset.aggregate(total=Sum('pending_balance'))['total'] or 0
        total_paid = self.queryset.aggregate(total=Sum('total_paid'))['total'] or 0
        total_cost = self.queryset.aggregate(total=Sum('total_projects_cost'))['total'] or 0

        return Response({
            'total_pending': float(total_pending),
            'total_paid': float(total_paid),
            'total_projects_cost': float(total_cost),
            'total_clients_with_balance': self.queryset.filter(pending_balance__gt=0).count()
        })


class RevenueViewSet(viewsets.ReadOnlyModelViewSet):
    """Revenue API ViewSet - Read Only"""
    queryset = Revenue.objects.select_related('client', 'project').all()
    serializer_class = RevenueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['revenue_id', 'client__name', 'project__name']
    ordering_fields = ['revenue_date', 'amount']

    def get_queryset(self):
        queryset = super().get_queryset()

        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)

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
            'total_revenue': float(total_revenue),
            'monthly_revenue': float(monthly_revenue),
            'total_records': self.queryset.count()
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


@staff_member_required
def financial_dashboard(request):
    """Professional Financial Dashboard"""
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)

    total_revenue = Revenue.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    current_month_revenue = Revenue.objects.filter(
        revenue_date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    last_month_revenue = Revenue.objects.filter(
        revenue_date__gte=last_month_start,
        revenue_date__lt=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    if last_month_revenue > 0:
        monthly_growth = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100
    else:
        monthly_growth = 100 if current_month_revenue > 0 else 0

    pending_payments = ClientBalance.objects.aggregate(total=Sum('pending_balance'))['total'] or Decimal('0.00')
    total_clients = Client.objects.filter(status='active').count()
    new_clients = Client.objects.filter(created_at__gte=start_of_month).count()
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(status='in_progress').count()
    completed_projects = Project.objects.filter(status='completed').count()
    net_profit = total_revenue
    profit_margin = 100 if total_revenue > 0 else 0

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

    top_clients = []
    client_balances = ClientBalance.objects.select_related('client').all()

    for cb in client_balances.order_by('-total_paid')[:5]:
        payment_percentage = (cb.total_paid / cb.total_projects_cost * 100) if cb.total_projects_cost > 0 else 0
        top_clients.append({
            'name': cb.client.name,
            'total_cost': cb.total_projects_cost,
            'total_paid': cb.total_paid,
            'pending': cb.pending_balance,
            'payment_percentage': payment_percentage
        })

    top_client_names = [c['name'] for c in top_clients[:5]]
    top_client_payments = [float(c['total_paid']) for c in top_clients[:5]]

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

    for status_item in project_statuses:
        project_status_labels.append(status_map.get(status_item['status'], status_item['status']))
        project_status_counts.append(status_item['count'])

    recent_invoices = Invoice.objects.select_related('client', 'project').all()[:10]

    total_employees = Employee.objects.filter(is_active=True).count()
    total_salary_expenses = SalaryPayment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

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
            'total_revenue': float(total_revenue),
            'pending_payments': float(pending_payments),
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
                'revenue': float(monthly_revenue)
            })

        return Response(monthly_data)


class ComprehensiveDashboardViewSet(viewsets.ViewSet):
    """Complete Dashboard API - Income, Expenses, Revenue all in one place"""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get complete financial summary"""
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        current_year = today.year

        total_revenue = Revenue.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        revenue_this_month = Revenue.objects.filter(
            revenue_date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        revenue_this_year = Revenue.objects.filter(
            revenue_date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        total_pending = Invoice.objects.filter(
            status__in=['unpaid', 'partial']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        total_clients = Client.objects.count()
        active_projects = Project.objects.filter(status='in_progress').count()
        total_projects = Project.objects.count()

        total_salary_paid = SalaryPayment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        salary_this_month = SalaryPayment.objects.filter(
            status='completed',
            payment_date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        salary_this_year = SalaryPayment.objects.filter(
            status='completed',
            payment_date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        pending_salary = SalaryPayment.objects.filter(
            status='pending'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_employees = Employee.objects.filter(is_active=True).count()

        recent_client_payments = Payment.objects.select_related(
            'client', 'project', 'invoice'
        ).order_by('-payment_date')[:10]
        recent_salary_payments = SalaryPayment.objects.select_related(
            'employee'
        ).order_by('-payment_date')[:10]
        recent_invoices = Invoice.objects.select_related(
            'client', 'project'
        ).order_by('-created_at')[:10]

        return Response({
            'total_revenue': float(total_revenue),
            'revenue_this_month': float(revenue_this_month),
            'revenue_this_year': float(revenue_this_year),
            'total_pending': float(total_pending),
            'total_clients': total_clients,
            'active_projects': active_projects,
            'total_projects': total_projects,
            'total_salary_paid': float(total_salary_paid),
            'salary_this_month': float(salary_this_month),
            'salary_this_year': float(salary_this_year),
            'pending_salary': float(pending_salary),
            'total_employees': total_employees,
            'net_income_all_time': float(total_revenue - total_salary_paid),
            'net_income_this_month': float(revenue_this_month - salary_this_month),
            'net_income_this_year': float(revenue_this_year - salary_this_year),
        })

    @action(detail=False, methods=['get'])
    def recent_payments(self, request):
        """Get all recent payment logs (income + expenses)"""
        client_payments = Payment.objects.select_related(
            'client', 'project', 'invoice'
        ).order_by('-payment_date')[:50]
        salary_payments = SalaryPayment.objects.select_related(
            'employee'
        ).order_by('-payment_date')[:50]

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
        today = timezone.now().date()
        monthly_data = []

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

            revenue = Revenue.objects.filter(
                revenue_date__gte=month_start,
                revenue_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

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
