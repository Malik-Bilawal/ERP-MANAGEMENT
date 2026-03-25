from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from unfold.admin import ModelAdmin
from rangefilter.filters import DateRangeFilter
from import_export.admin import ImportExportModelAdmin
from .models import Invoice, Revenue, ClientBalance, CompanyRevenue
from client_management.models import Project

@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = [
        'invoice_id', 'client_link', 'project_link', 'amount_display', 
        'invoice_date', 'payment_status', 'created_at'
    ]
    list_filter = ['invoice_date', 'client']
    search_fields = ['invoice_id', 'invoice_number', 'client__name', 'project__name']
    list_per_page = 20
    raw_id_fields = ['client', 'project', 'created_by']
    readonly_fields = ['invoice_id', 'invoice_number', 'created_at']
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_id', 'invoice_number', 'client', 'project')
        }),
        ('Payment Details', {
            'fields': ('amount', 'invoice_date'),
            'description': 'Amount is auto-populated from project cost'
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def client_link(self, obj):
        return format_html('<a href="/admin/client_management/client/{}/change/">{}</a>', 
                          obj.client.id, obj.client.name)
    client_link.short_description = "Client"
    
    def project_link(self, obj):
        return format_html('<a href="/admin/client_management/project/{}/change/">{}</a>', 
                          obj.project.id, obj.project.name)
    project_link.short_description = "Project"
    
    def amount_display(self, obj):
    # Format the number as a string first (with commas and 2 decimal places)
     formatted_value = f"{obj.amount:,.2f}"
    
    # Pass the already-formatted string into format_html
     return format_html(
        '<span style="font-weight: bold; color: #2ecc71;">${}</span>', 
        formatted_value
    )
    amount_display.short_description = "Amount Paid"
    
    def payment_status(self, obj):
        return format_html('<span style="color: #27ae60; font-weight: bold;">✓ PAID</span>')
    payment_status.short_description = "Status"
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Auto-populate amount when project is selected
        if 'project' in form.base_fields:
            form.base_fields['project'].widget.attrs.update({
                'onchange': 'fetchProjectCost(this.value)'
            })
        return form
    
    class Media:
        js = ('admin/js/invoice_autofill.js',)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Revenue)
class RevenueAdmin(ModelAdmin):
    list_display = ['revenue_id', 'client_link', 'project_link', 'amount_display', 'revenue_date', 'invoice_link']
    list_filter = [('revenue_date', DateRangeFilter), 'client']
    search_fields = ['revenue_id', 'client__name', 'project__name', 'invoice__invoice_id']
    list_per_page = 20
    raw_id_fields = ['client', 'project', 'invoice']
    readonly_fields = ['revenue_id', 'created_at']
    
    def client_link(self, obj):
        return format_html('<a href="/admin/client_management/client/{}/change/">{}</a>', 
                          obj.client.id, obj.client.name)
    client_link.short_description = "Client"
    
    def project_link(self, obj):
        return format_html('<a href="/admin/client_management/project/{}/change/">{}</a>', 
                          obj.project.id, obj.project.name)
    project_link.short_description = "Project"
    
    def amount_display(self, obj):
        # Handle None check just in case, then format as currency string
        formatted_value = f"{obj.amount:,.2f}" if obj.amount is not None else "0.00"
        
        # Pass the pre-formatted string to the template
        return format_html('<b>${}</b>', formatted_value)
    
    amount_display.short_description = "Revenue"
    
    def invoice_link(self, obj):
        return format_html('<a href="/admin/financial/invoice/{}/change/">View Invoice</a>', obj.invoice.id)
    invoice_link.short_description = "Invoice"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ClientBalance)
class ClientBalanceAdmin(ModelAdmin):
    list_display = ['client_link', 'total_projects_cost_display', 'total_paid_display', 'pending_balance_display', 'payment_percentage', 'last_updated']
    search_fields = ['client__name', 'client__email']
    raw_id_fields = ['client']
    readonly_fields = ['last_updated']
    
    fieldsets = (
        ('Client Information', {
            'fields': ('client',)
        }),
        ('Financial Summary', {
            'fields': ('opening_balance', 'total_projects_cost', 'total_invoiced', 'pending_balance'),
            'description': 'Pending Balance = Total Projects Cost - Total Paid'
        }),
        ('Metadata', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )
    
    def client_link(self, obj):
        return format_html('<a href="/admin/client_management/client/{}/change/"><b>{}</b></a>', 
                          obj.client.id, obj.client.name)
    client_link.short_description = "Client"
    
    def total_projects_cost_display(self, obj):
        val = f"{obj.total_projects_cost:,.2f}" if obj.total_projects_cost else "0.00"
        return format_html('<b>${}</b>', val)
    total_projects_cost_display.short_description = "Total Projects Cost"
    
    def total_paid_display(self, obj):
        val = f"{obj.total_invoiced:,.2f}" if obj.total_invoiced else "0.00"
        return format_html('<span style="color: #27ae60;">${}</span>', val)
    total_paid_display.short_description = "Total Paid"
    
    def pending_balance_display(self, obj):
        val = f"{obj.pending_balance:,.2f}" if obj.pending_balance else "0.00"
        if obj.pending_balance and obj.pending_balance > 0:
            return format_html('<span style="color: #e74c3c; font-weight: bold;">${}</span>', val)
        return format_html('<span style="color: #27ae60;">${}</span>', val)
    pending_balance_display.short_description = "Pending Balance"
    
    def payment_percentage(self, obj):
        if obj.total_projects_cost and obj.total_projects_cost > 0:
            percentage = (obj.total_invoiced / obj.total_projects_cost) * 100
            color = '#27ae60' if percentage >= 100 else '#f39c12'
            # Format the percentage to 1 decimal place here
            val = f"{percentage:.1f}%"
            return format_html('<span style="color: {};">{}</span>', color, val)
        return '0%'
    payment_percentage.short_description = "Payment %"


@admin.register(CompanyRevenue)
class CompanyRevenueAdmin(ModelAdmin):
    list_display = ['date', 'total_revenue_display', 'total_clients', 'total_projects', 'active_projects']
    list_filter = [('date', DateRangeFilter)]
    readonly_fields = ['revenue_id', 'updated_at']
    
    def total_revenue_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #2ecc71;">${:,.2f}</span>', obj.total_revenue)
    total_revenue_display.short_description = "Total Revenue"
    
    def has_add_permission(self, request):
        return False