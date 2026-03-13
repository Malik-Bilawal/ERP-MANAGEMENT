# salary/admin.py
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import SalaryStructure, SalaryAssignment, SalarySlip, StaffInvoice, InvoiceLineItem

@admin.register(SalaryStructure)
class SalaryStructureAdmin(ModelAdmin):
    list_display = ['name', 'basic_percentage', 'hra_percentage', 'pf_percentage', 'is_active_badge']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Earnings Components', {
            'fields': (
                ('basic_percentage', 'hra_percentage'),
                ('conveyance_allowance', 'medical_allowance'),
                'special_allowance'
            ),
        }),
        ('Deduction Components', {
            'fields': (
                ('pf_percentage', 'esi_percentage'),
                ('professional_tax', 'tds_percentage'),
            ),
        }),
    )
    
    @display(description="Status")
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="bg-green-100 text-green-800 px-2 py-1 rounded">Active</span>')
        return format_html('<span class="bg-gray-100 text-gray-800 px-2 py-1 rounded">Inactive</span>')

@admin.register(SalaryAssignment)
class SalaryAssignmentAdmin(ModelAdmin):
    list_display = ['staff', 'salary_structure', 'effective_from', 'effective_to', 'is_current_badge']
    list_filter = ['is_current', 'salary_structure']
    search_fields = ['staff__first_name', 'staff__last_name']
    autocomplete_fields = ['staff', 'salary_structure']
    date_hierarchy = 'effective_from'
    
    @display(description="Current")
    def is_current_badge(self, obj):
        if obj.is_current:
            return format_html('<span class="bg-green-100 text-green-800 px-2 py-1 rounded">✓ Current</span>')
        return format_html('<span class="bg-gray-100 text-gray-800 px-2 py-1 rounded">Past</span>')

@admin.register(SalarySlip)
class SalarySlipAdmin(ModelAdmin):
    list_display = [
        'staff', 'month_display', 'gross_earnings_display', 
        'total_deductions_display', 'net_pay_display', 'status_badge'
    ]
    list_filter = ['status', 'month']
    search_fields = ['staff__first_name', 'staff__last_name']
    autocomplete_fields = ['staff', 'salary_structure', 'generated_by']
    date_hierarchy = 'month'
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('staff', 'salary_structure', 'month')
        }),
        ('Earnings', {
            'fields': (
                ('basic', 'hra'),
                ('conveyance', 'medical'),
                ('special', 'overtime'),
                ('bonus', 'other_earnings'),
            ),
        }),
        ('Deductions', {
            'fields': (
                ('pf', 'esi'),
                ('professional_tax', 'tds'),
                ('loan_deduction', 'advance_deduction'),
                'other_deductions',
            ),
        }),
        ('Totals', {
            'fields': (
                ('gross_earnings', 'total_deductions'),
                'net_pay',
            ),
        }),
        ('Attendance', {
            'fields': (
                ('working_days', 'days_present'),
                ('days_absent', 'leave_taken'),
                'overtime_hours',
            ),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('status', 'payment_date', 'payment_reference', 'notes'),
        }),
        ('System Info', {
            'fields': ('generated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    @display(description="Month")
    def month_display(self, obj):
        return obj.month.strftime('%B %Y')
    
    @display(description="Gross")
    def gross_earnings_display(self, obj):
        return format_html('₹{:,.2f}', obj.gross_earnings)
    
    @display(description="Deductions")
    def total_deductions_display(self, obj):
        return format_html('₹{:,.2f}', obj.total_deductions)
    
    @display(description="Net Pay")
    def net_pay_display(self, obj):
        return format_html('<span class="font-bold">₹{:,.2f}</span>', obj.net_pay)
    
    @display(description="Status")
    def status_badge(self, obj):
        colors = {
            'draft': 'bg-gray-100 text-gray-800',
            'approved': 'bg-blue-100 text-blue-800',
            'paid': 'bg-green-100 text-green-800',
            'cancelled': 'bg-red-100 text-red-800',
        }
        return format_html(
            '<span class="{} px-2 py-1 rounded text-xs font-medium">{}</span>',
            colors.get(obj.status, 'bg-gray-100 text-gray-800'),
            obj.get_status_display()
        )
    
    actions = ['mark_as_approved', 'mark_as_paid']
    
    def mark_as_approved(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} salary slips marked as approved")
    mark_as_approved.short_description = "Mark selected as Approved"
    
    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid')
        self.message_user(request, f"{queryset.count()} salary slips marked as paid")
    mark_as_paid.short_description = "Mark selected as Paid"

# In salary/admin.py - update the StaffInvoiceAdmin class

@admin.register(StaffInvoice)
class StaffInvoiceAdmin(ModelAdmin):
    list_display = [
        'invoice_number', 'staff', 'project', 'invoice_date',
        'due_date', 'total_amount_display', 'status_badge', 'balance_due_display'
    ]
    list_filter = ['status', 'invoice_date']
    search_fields = ['invoice_number', 'staff__first_name', 'staff__last_name']
    autocomplete_fields = ['staff', 'project', 'created_by']
    date_hierarchy = 'invoice_date'
    
    # CORRECTED FIELDSETS - no duplicates
    fieldsets = (
        ('Invoice Information', {
            'fields': (
                'invoice_number', 'staff', 'project',
                ('invoice_date', 'due_date'),
                ('period_start', 'period_end'),
            )
        }),
        ('Financial Details', {
            'fields': (
                ('subtotal', 'tax_rate', 'tax_amount'),
                ('discount', 'total_amount'),
                ('paid_amount',),
            ),
        }),
        ('Work Details', {
            'fields': (
                ('hours_worked', 'hourly_rate'),
                'description',
            ),
        }),
        ('Status', {
            'fields': ('status', 'notes', 'payment_date', 'payment_method', 'transaction_id'),
        }),
        ('System Info', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # Keep your display methods
    @display(description="Total")
    def total_amount_display(self, obj):
        return format_html('₹{:,.2f}', obj.total_amount)
    
    @display(description="Balance")
    def balance_due_display(self, obj):
        if obj.balance_due > 0:
            return format_html('<span class="text-red-600 font-bold">₹{:,.2f}</span>', obj.balance_due)
        return format_html('<span class="text-green-600">✓ Paid</span>')
    
    @display(description="Status")
    def status_badge(self, obj):
        colors = {
            'draft': 'bg-gray-100 text-gray-800',
            'sent': 'bg-blue-100 text-blue-800',
            'paid': 'bg-green-100 text-green-800',
            'overdue': 'bg-red-100 text-red-800',
            'cancelled': 'bg-gray-100 text-gray-500',
        }
        badge_text = obj.get_status_display()
        if obj.is_overdue and obj.status != 'paid':
            badge_text = 'OVERDUE'
            colors['overdue'] = 'bg-red-500 text-white'
        
        return format_html(
            '<span class="{} px-2 py-1 rounded text-xs font-medium">{}</span>',
            colors.get(obj.status, 'bg-gray-100 text-gray-800'),
            badge_text
        )
    
@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'unit_price_display', 'amount_display']
    list_filter = ['invoice__status']
    search_fields = ['description', 'invoice__invoice_number']
    autocomplete_fields = ['invoice']
    
    @display(description="Unit Price")
    def unit_price_display(self, obj):
        return format_html('₹{:,.2f}', obj.unit_price)
    
    @display(description="Amount")
    def amount_display(self, obj):
        return format_html('₹{:,.2f}', obj.amount)