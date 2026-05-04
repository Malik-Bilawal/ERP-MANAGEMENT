from decimal import Decimal
from django.contrib import admin
from django.urls import reverse
from django.urls import path as url_path
from django.utils.html import format_html
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404
from unfold.admin import ModelAdmin, TabularInline
from .models import (
    EmployeeRole, Employee, SalaryPayment, SalaryRecord, 
    ExpenseCategory, MonthlyExpensePlan, ActualExpense,
    ProjectAssignment, ProjectManager, EmployeeBenefit, EmployeeLedger
)


class ProjectAssignmentInline(TabularInline):
    model = ProjectAssignment
    extra = 1
    fields = ('employee', 'role_on_project', 'hours_per_week', 'is_primary', 'start_date', 'end_date', 'is_active')
    autocomplete_fields = ['employee']


class ProjectManagerInline(TabularInline):
    model = ProjectManager
    extra = 1
    fields = ('employee', 'assigned_date', 'is_active')
    autocomplete_fields = ['employee']


class EmployeeBenefitInline(TabularInline):
    model = EmployeeBenefit
    extra = 1
    fields = ('benefit_type', 'annual_limit', 'used_amount', 'start_date', 'end_date', 'is_active')
    readonly_fields = ['used_amount']


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(ModelAdmin):
    list_display = ['name', 'expense_type', 'is_active', 'created_at']
    list_filter = ['expense_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(MonthlyExpensePlan)
class MonthlyExpensePlanAdmin(ModelAdmin):
    list_display = ['plan_id', 'month', 'total_planned_display', 'actual_display', 'remaining_display', 'status_badge', 'created_at']
    list_filter = ['status', 'month']
    search_fields = ['plan_id', 'month']
    readonly_fields = ['plan_id', 'total_planned', 'created_at', 'updated_at']
    list_per_page = 20
    
    def total_planned_display(self, obj):
        return format_html('<span style="font-weight: bold;">${}</span>', "{:,.2f}".format(float(obj.total_planned)))
    total_planned_display.short_description = "Total Planned"
    
    def actual_display(self, obj):
        actual = obj.actual_expenses['total']
        return format_html('<span>${}</span>', "{:,.2f}".format(float(actual)))
    actual_display.short_description = "Actual Spent"
    
    def remaining_display(self, obj):
        remaining = obj.remaining_budget
        color = '#2ecc71' if remaining >= 0 else '#e74c3c'
        return format_html('<span style="color: {}; font-weight: bold;">${}</span>', color, "{:,.2f}".format(float(remaining)))
    remaining_display.short_description = "Remaining"
    
    def status_badge(self, obj):
        colors = {'draft': '#95a5a6', 'planned': '#3498db', 'approved': '#f39c12', 'completed': '#2ecc71', 'cancelled': '#e74c3c'}
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.get_status_display().upper()
        )
    status_badge.short_description = "Status"
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('plan_id', 'month', 'status', 'notes')
        }),
        ('Planned Expenses', {
            'fields': ('planned_salary', 'planned_bonus', 'planned_medical', 'planned_travel', 'planned_equipment', 'planned_training', 'planned_other', 'total_planned'),
            'description': 'Plan your expenses for the month'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmployeeRole)
class EmployeeRoleAdmin(ModelAdmin):
    list_display = ['role_name', 'description_display', 'employee_count', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['role_name', 'description']
    
    def description_display(self, obj):
        return obj.description[:50] + '...' if obj.description and len(obj.description) > 50 else obj.description
    description_display.short_description = "Description"
    
    def employee_count(self, obj):
        return obj.employees.count()
    employee_count.short_description = "Employees"


@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    list_display = ['employee_id', 'full_name_display', 'email', 'role_display', 'salary_display', 'employment_type_display', 'joining_date', 'status_badge', 'show_ledger_link']
    list_filter = ['employment_type', 'role', 'is_active', 'joining_date']
    search_fields = ['employee_id', 'first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['employee_id', 'created_at', 'updated_at']
    raw_id_fields = ['user']
    list_per_page = 20
    
    def full_name_display(self, obj):
        return format_html('<strong>{}</strong>', obj.full_name)
    full_name_display.short_description = "Name"
    
    def role_display(self, obj):
        return obj.role.role_name
    role_display.short_description = "Role"
    
    def salary_display(self, obj):
        return format_html('<span style="color: #e74c3c;">${}</span>', "{:,.2f}".format(float(obj.salary)))
    salary_display.short_description = "Salary"
    
    def employment_type_display(self, obj):
        return obj.get_employment_type_display()
    employment_type_display.short_description = "Type"
    
    def status_badge(self, obj):
        color = '#2ecc71' if obj.is_active else '#95a5a6'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, status
        )
    status_badge.short_description = "Status"
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee_id', 'user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Employment Details', {
            'fields': ('role', 'employment_type', 'salary', 'joining_date', 'is_active')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'account_number', 'ifsc_code'),
            'classes': ('collapse',)
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',)
        }),
        ('Address & Notes', {
            'fields': ('address', 'notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [EmployeeBenefitInline]
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url_path('<int:employee_id>/ledger/', self.admin_site.admin_view(self.employee_ledger_view), name='employee_ledger'),
        ]
        return custom_urls + urls
    
    def employee_ledger_view(self, request, employee_id):
        employee = get_object_or_404(Employee, pk=employee_id)
        
        ledger_entries = EmployeeLedger.objects.filter(employee=employee).order_by('-transaction_date', '-created_at')
        salary_payments = SalaryPayment.objects.filter(employee=employee).order_by('-payment_date')
        expenses = ActualExpense.objects.filter(employee=employee).order_by('-expense_date')
        benefits = EmployeeBenefit.objects.filter(employee=employee, is_active=True)
        
        total_earned = ledger_entries.filter(transaction_type='salary').aggregate(total=Sum('debit'))['total'] or Decimal('0.00')
        total_paid = ledger_entries.filter(transaction_type='salary').aggregate(total=Sum('credit'))['total'] or Decimal('0.00')
        pending = total_earned - total_paid
        
        context = {
            **self.admin_site.each_context(request),
            'employee': employee,
            'ledger_entries': ledger_entries,
            'salary_payments': salary_payments,
            'expenses': expenses,
            'benefits': benefits,
            'total_earned': total_earned,
            'total_paid': total_paid,
            'pending': pending,
            'title': f'Ledger - {employee.full_name}',
        }
        
        return render(request, 'hr/employee_ledger.html', context)
    
    def show_ledger_link(self, obj):
        url = reverse('admin:employee_ledger', args=[obj.id])
        return format_html(
            '<a href="{}" style="background: #3b82f6; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 500; display: inline-block;">Show Ledger</a>',
            url
        )
    show_ledger_link.short_description = "Actions"


@admin.register(SalaryPayment)
class SalaryPaymentAdmin(ModelAdmin):
    list_display = ['payment_id', 'employee_link', 'salary_info', 'amount_display', 'paid_display', 'remaining_display', 'month_display', 'status_badge', 'payment_date']
    list_filter = ['status', 'payment_date', 'month']
    search_fields = ['payment_id', 'employee__first_name', 'employee__last_name', 'transaction_reference']
    readonly_fields = ['payment_id', 'created_at', 'updated_at', 'salary_info_display', 'total_paid_display', 'remaining_display']
    raw_id_fields = ['employee', 'created_by']
    list_per_page = 20
    date_hierarchy = 'payment_date'
    
    def employee_link(self, obj):
        return format_html('<a href="/admin/hr/employee/{}/change/"><strong>{}</strong></a>', 
                          obj.employee.id, obj.employee.full_name)
    employee_link.short_description = "Employee"
    
    def salary_info(self, obj):
        return format_html('<span>${}</span>/month', "{:,.2f}".format(float(obj.employee.salary)))
    salary_info.short_description = "Salary"
    
    def amount_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #e74c3c;">${}</span>', "{:,.2f}".format(float(obj.amount)))
    amount_display.short_description = "Amount"
    
    def paid_display(self, obj):
        paid = obj.employee.salary_payments.filter(status='completed').exclude(id=obj.id).aggregate(total=Sum('amount'))['total'] or 0
        return format_html('<span style="color: #2ecc71;">${}</span>', "{:,.2f}".format(float(paid)))
    paid_display.short_description = "Already Paid"
    
    def remaining_display(self, obj):
        paid = obj.employee.salary_payments.filter(status='completed').exclude(id=obj.id).aggregate(total=Sum('amount'))['total'] or 0
        remaining = float(obj.employee.salary) - float(paid) - float(obj.amount)
        if remaining > 0:
            return format_html('<span style="color: #e74c3c;">${}</span>', "{:,.2f}".format(remaining))
        return format_html('<span style="color: #2ecc71;">{}</span>', 'Paid')
    remaining_display.short_description = "After This"
    
    def month_display(self, obj):
        return obj.month.strftime('%B %Y')
    month_display.short_description = "Month"
    
    def status_badge(self, obj):
        colors = {'pending': '#f39c12', 'processing': '#3498db', 'completed': '#2ecc71', 'cancelled': '#e74c3c'}
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.get_status_display().upper()
        )
    status_badge.short_description = "Status"
    
    def salary_info_display(self, obj):
        return format_html('''
            <div style="padding: 10px; background: #f8f9fa; border-radius: 8px;">
                <strong>Employee:</strong> {}<br>
                <strong>Monthly Salary:</strong> ${:,.2f}<br>
                <strong>Employment Type:</strong> {}
            </div>
        ''', obj.employee.full_name, float(obj.employee.salary), obj.employee.get_employment_type_display())
    salary_info_display.short_description = "Employee Info"
    
    def total_paid_display(self, obj):
        paid = obj.employee.salary_payments.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
        return format_html('<span>${:,.2f}</span>', float(paid))
    total_paid_display.short_description = "Total Paid (All Time)"
    
    fieldsets = (
        ('Employee & Month', {
            'fields': ('payment_id', 'employee', 'month', 'salary_info_display')
        }),
        ('Payment Amount', {
            'fields': ('amount', 'total_paid_display', 'remaining_display'),
            'description': 'Enter the amount you are paying now. Remaining shows balance after this payment.'
        }),
        ('Payment Details', {
            'fields': ('status', 'payment_method', 'payment_date', 'transaction_reference')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SalaryRecord)
class SalaryRecordAdmin(ModelAdmin):
    list_display = ['employee_link', 'month_display', 'base_salary_display', 'bonus_display', 'deductions_display', 'net_salary_display', 'paid_status']
    list_filter = ['month', 'is_paid']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['employee']
    list_per_page = 20
    
    def employee_link(self, obj):
        return format_html('<a href="/admin/hr/employee/{}/change/">{}</a>', 
                          obj.employee.id, obj.employee.full_name)
    employee_link.short_description = "Employee"
    
    def month_display(self, obj):
        return obj.month.strftime('%B %Y')
    month_display.short_description = "Month"
    
    def base_salary_display(self, obj):
        return format_html('<span>${}</span>', "{:,.2f}".format(float(obj.base_salary)))
    base_salary_display.short_description = "Base Salary"
    
    def bonus_display(self, obj):
        return format_html('<span style="color: #2ecc71;">${}</span>', "{:,.2f}".format(float(obj.bonus)))
    bonus_display.short_description = "Bonus"
    
    def deductions_display(self, obj):
        return format_html('<span style="color: #e74c3c;">-${}</span>', "{:,.2f}".format(float(obj.deductions)))
    deductions_display.short_description = "Deductions"
    
    def net_salary_display(self, obj):
        return format_html('<strong>${}</strong>', "{:,.2f}".format(float(obj.net_salary)))
    net_salary_display.short_description = "Net Salary"
    
    def paid_status(self, obj):
        color = '#2ecc71' if obj.is_paid else '#f39c12'
        status = 'Paid' if obj.is_paid else 'Pending'
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, status
        )
    paid_status.short_description = "Status"


@admin.register(ActualExpense)
class ActualExpenseAdmin(ModelAdmin):
    list_display = ['expense_id', 'category_display', 'amount_display', 'employee_display', 'expense_month_display', 'status_badge', 'expense_date']
    list_filter = ['status', 'category', 'expense_month']
    search_fields = ['expense_id', 'description', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['expense_id', 'created_at', 'updated_at']
    raw_id_fields = ['employee', 'created_by']
    list_per_page = 20
    date_hierarchy = 'expense_date'
    
    def category_display(self, obj):
        return format_html('<span>{}</span>', obj.category.name)
    category_display.short_description = "Category"
    
    def amount_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #e74c3c;">${}</span>', "{:,.2f}".format(float(obj.amount)))
    amount_display.short_description = "Amount"
    
    def employee_display(self, obj):
        if obj.employee:
            return format_html('<a href="/admin/hr/employee/{}/change/">{}</a>', 
                              obj.employee.id, obj.employee.full_name)
        return "-"
    employee_display.short_description = "Employee"
    
    def expense_month_display(self, obj):
        return obj.expense_month.strftime('%B %Y')
    expense_month_display.short_description = "Month"
    
    def status_badge(self, obj):
        colors = {'pending': '#f39c12', 'approved': '#3498db', 'completed': '#2ecc71', 'cancelled': '#e74c3c'}
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.get_status_display().upper()
        )
    status_badge.short_description = "Status"
    
    fieldsets = (
        ('Expense Information', {
            'fields': ('expense_id', 'expense_month', 'category', 'amount', 'description')
        }),
        ('Details', {
            'fields': ('status', 'expense_date', 'employee', 'transaction_reference', 'receipt')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProjectAssignment)
class ProjectAssignmentAdmin(ModelAdmin):
    list_display = ['assignment_id', 'employee_link', 'project_link', 'role_on_project', 'hours_per_week', 'is_primary', 'is_active', 'start_date']
    list_filter = ['is_active', 'is_primary', 'start_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'project__name']
    readonly_fields = ['assignment_id', 'created_at', 'updated_at']
    autocomplete_fields = ['employee']
    list_per_page = 20
    
    def employee_link(self, obj):
        url = reverse('admin:hr_employee_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee.full_name)
    employee_link.short_description = "Employee"
    
    def project_link(self, obj):
        url = reverse('admin:client_management_project_change', args=[obj.project.id])
        return format_html('<a href="{}">{}</a>', url, obj.project.name)
    project_link.short_description = "Project"


@admin.register(ProjectManager)
class ProjectManagerAdmin(ModelAdmin):
    list_display = ['employee_link', 'project_link', 'assigned_date', 'is_active']
    list_filter = ['is_active', 'assigned_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'project__name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['employee']
    list_per_page = 20
    
    def employee_link(self, obj):
        url = reverse('admin:hr_employee_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee.full_name)
    employee_link.short_description = "Employee"
    
    def project_link(self, obj):
        url = reverse('admin:client_management_project_change', args=[obj.project.id])
        return format_html('<a href="{}">{}</a>', url, obj.project.name)
    project_link.short_description = "Project"


@admin.register(EmployeeBenefit)
class EmployeeBenefitAdmin(ModelAdmin):
    list_display = ['benefit_id', 'employee_link', 'benefit_type_display', 'annual_limit_display', 'used_amount_display', 'remaining_display', 'utilization_display', 'is_active']
    list_filter = ['benefit_type', 'is_active', 'start_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'description']
    readonly_fields = ['benefit_id', 'used_amount', 'remaining_display', 'utilization_display', 'created_at', 'updated_at']
    list_per_page = 20
    
    def employee_link(self, obj):
        url = reverse('admin:hr_employee_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee.full_name)
    employee_link.short_description = "Employee"
    
    def benefit_type_display(self, obj):
        return obj.get_benefit_type_display()
    benefit_type_display.short_description = "Type"
    
    def annual_limit_display(self, obj):
        return format_html('<span style="font-weight: bold;">${}</span>', "{:,.2f}".format(float(obj.annual_limit)))
    annual_limit_display.short_description = "Annual Limit"
    
    def used_amount_display(self, obj):
        return format_html('<span style="color: #e74c3c;">${}</span>', "{:,.2f}".format(float(obj.used_amount)))
    used_amount_display.short_description = "Used"
    
    def remaining_display(self, obj):
        remaining = obj.remaining
        color = '#2ecc71' if remaining > 0 else '#e74c3c'
        return format_html('<span style="color: {}; font-weight: bold;">${}</span>', color, "{:,.2f}".format(float(remaining)))
    remaining_display.short_description = "Remaining"
    
    def utilization_display(self, obj):
        pct = obj.utilization_percentage
        color = '#e74c3c' if pct > 80 else '#f39c12' if pct > 50 else '#2ecc71'
        return format_html('<span style="color: {}; font-weight: bold;">{}%</span>', color, "{:.1f}".format(float(pct)))
    utilization_display.short_description = "Usage %"


@admin.register(EmployeeLedger)
class EmployeeLedgerAdmin(ModelAdmin):
    list_display = ['employee_link', 'transaction_type_display', 'description', 'debit_display', 'credit_display', 'running_balance_display', 'transaction_date']
    list_filter = ['transaction_type', 'transaction_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'description']
    readonly_fields = ['created_at']
    list_per_page = 20
    date_hierarchy = 'transaction_date'
    
    def employee_link(self, obj):
        url = reverse('admin:hr_employee_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee.full_name)
    employee_link.short_description = "Employee"
    
    def transaction_type_display(self, obj):
        return obj.get_transaction_type_display()
    transaction_type_display.short_description = "Type"
    
    def debit_display(self, obj):
        if obj.debit > 0:
            return format_html('<span style="color: #e74c3c;">${}</span>', "{:,.2f}".format(float(obj.debit)))
        return "-"
    debit_display.short_description = "Debit"
    
    def credit_display(self, obj):
        if obj.credit > 0:
            return format_html('<span style="color: #2ecc71;">${}</span>', "{:,.2f}".format(float(obj.credit)))
        return "-"
    credit_display.short_description = "Credit"
    
    def running_balance_display(self, obj):
        color = '#e74c3c' if obj.running_balance > 0 else '#2ecc71'
        return format_html('<span style="color: {}; font-weight: bold;">${}</span>', color, "{:,.2f}".format(float(obj.running_balance)))
    running_balance_display.short_description = "Balance"


class HRDashboardAdmin(ModelAdmin):
    """Custom admin view for HR Dashboard"""
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            url_path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='hr_dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        from django.db.models import Count, Avg
        from client_management.models import Project
        from financial.models import CompanyRevenue
        
        today = timezone.now().date()
        
        active_employees = Employee.objects.filter(is_active=True).count()
        total_employees = Employee.objects.count()
        total_monthly_salary = Employee.objects.filter(is_active=True).aggregate(total=Sum('salary'))['total'] or Decimal('0.00')
        
        active_projects = Project.objects.filter(status='in_progress').count()
        total_projects = Project.objects.count()
        
        total_assignments = ProjectAssignment.objects.filter(is_active=True).count()
        total_managers = ProjectManager.objects.filter(is_active=True).count()
        
        active_benefits = EmployeeBenefit.objects.filter(is_active=True).count()
        total_benefit_limit = EmployeeBenefit.objects.filter(is_active=True).aggregate(total=Sum('annual_limit'))['total'] or Decimal('0.00')
        total_benefit_used = EmployeeBenefit.objects.filter(is_active=True).aggregate(total=Sum('used_amount'))['total'] or Decimal('0.00')
        
        salary_this_month = SalaryPayment.objects.filter(
            status='completed',
            payment_date__month=today.month,
            payment_date__year=today.year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        expenses_this_month = ActualExpense.objects.filter(
            status='completed',
            expense_date__month=today.month,
            expense_date__year=today.year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        recent_revenue = list(CompanyRevenue.objects.order_by('-date')[:7])
        total_revenue = sum(r.total_revenue for r in recent_revenue)
        total_expenses = sum(r.total_expenses for r in recent_revenue)
        net_profit = total_revenue - total_expenses
        
        employee_utilization = []
        for emp in Employee.objects.filter(is_active=True)[:10]:
            assignments = ProjectAssignment.objects.filter(employee=emp, is_active=True)
            total_hours = assignments.aggregate(total=Sum('hours_per_week'))['total'] or 0
            utilization = min((total_hours / 40) * 100, 100) if total_hours > 0 else 0
            employee_utilization.append({
                'employee': emp,
                'hours': total_hours,
                'utilization': utilization,
                'projects': assignments.count(),
            })
        
        context = {
            **self.admin_site.each_context(request),
            'active_employees': active_employees,
            'total_employees': total_employees,
            'total_monthly_salary': total_monthly_salary,
            'active_projects': active_projects,
            'total_projects': total_projects,
            'total_assignments': total_assignments,
            'total_managers': total_managers,
            'active_benefits': active_benefits,
            'total_benefit_limit': total_benefit_limit,
            'total_benefit_used': total_benefit_used,
            'salary_this_month': salary_this_month,
            'expenses_this_month': expenses_this_month,
            'recent_revenue': recent_revenue,
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'employee_utilization': employee_utilization,
            'title': 'HR Dashboard',
        }
        
        return render(request, 'hr/dashboard.html', context)


admin.site.register_view = lambda *args, **kwargs: lambda f: f