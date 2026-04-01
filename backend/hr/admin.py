from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from unfold.admin import ModelAdmin
from .models import EmployeeRole, Employee, SalaryPayment, SalaryRecord, ExpenseCategory, MonthlyExpensePlan


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
            'fields': ('planned_salary', 'planned_bonus', 'planned_medical', 'planned_travel', 'planned_other', 'total_planned'),
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
    list_display = ['employee_id', 'full_name_display', 'email', 'role_display', 'salary_display', 'employment_type_display', 'joining_date', 'status_badge']
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
        return format_html('<span style="color: #2ecc71;">Paid</span>')
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