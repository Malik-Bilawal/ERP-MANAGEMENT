# core/admin.py
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.db.models import Sum, Count
from django.views.generic import TemplateView
from datetime import timedelta
from decimal import Decimal
from unfold.admin import ModelAdmin
from unfold.views import UnfoldModelAdminViewMixin
from .models import CompanySettings
from client_management.models import Client, Project
from financial.models import Revenue, ClientBalance, Invoice, Payment
from hr.models import Employee, SalaryPayment


class FinancialDashboardView(UnfoldModelAdminViewMixin, TemplateView):
    """Financial Dashboard using Unfold's recommended pattern"""
    title = "Financial Dashboard"
    permission_required = ()
    template_name = "admin/financial/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        
        # Net Profit (Revenue - Salary Expenses)
        total_salary_expenses = SalaryPayment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        net_profit = total_revenue - total_salary_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
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
        
        for cb in client_balances.order_by('-total_paid')[:5]:
            payment_percentage = (cb.total_paid / cb.total_projects_cost * 100) if cb.total_projects_cost > 0 else 0
            top_clients.append({
                'name': cb.client.name,
                'total_cost': cb.total_projects_cost,
                'total_paid': cb.total_paid,
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
        
        # Total employees
        total_employees = Employee.objects.filter(is_active=True).count()
        
        context.update({
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
            'completed_projects': completed_projects,
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
        })
        
        return context


# Register the dashboard view with a dummy model admin
@admin.register(CompanySettings)
class CompanySettingsAdmin(ModelAdmin):
    list_display = ['company_name', 'email', 'phone', 'currency']
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'company_logo', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address',)
        }),
        ('Tax & Financial', {
            'fields': ('tax_number', 'fiscal_year_start', 'currency')
        }),
    )
    
    def has_add_permission(self, request):
        # Prevent adding multiple settings
        if CompanySettings.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('financial-dashboard/',
                 self.admin_site.admin_view(FinancialDashboardView.as_view(model_admin=self)),
                 name='financial_dashboard_unfold'),
        ]
        return custom_urls + urls