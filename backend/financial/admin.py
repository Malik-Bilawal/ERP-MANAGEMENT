from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from unfold.admin import ModelAdmin
from .models import Invoice, Revenue, ClientBalance, CompanyRevenue, Payment
from django import forms


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['invoice'].widget.attrs['data-invoice-change'] = 'true'


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ['invoice_id', 'client_link', 'project_link', 'amount_display', 'amount_paid_display', 'remaining_display', 'status_badge', 'invoice_date', 'actions_column']
    list_filter = ['status', 'invoice_date', 'client']
    search_fields = ['invoice_id', 'invoice_number', 'client__name', 'project__name']
    readonly_fields = ['invoice_id', 'invoice_number', 'created_at']
    raw_id_fields = ['client', 'project', 'created_by']
    list_per_page = 20
    
    def client_link(self, obj):
        return format_html('<a href="/admin/client_management/client/{}/change/">{}</a>', 
                          obj.client.id, obj.client.name)
    client_link.short_description = "Client"
    
    def project_link(self, obj):
        return format_html('<a href="/admin/client_management/project/{}/change/">{}</a>', 
                          obj.project.id, obj.project.name)
    project_link.short_description = "Project"
    
    def amount_display(self, obj):
        return format_html('<span style="font-weight: bold;">${}</span>', "{:,.2f}".format(float(obj.amount)))
    amount_display.short_description = "Total Amount"
    
    def amount_paid_display(self, obj):
        return format_html('<span style="color: #2ecc71;">${}</span>', "{:,.2f}".format(float(obj.amount_paid)))
    amount_paid_display.short_description = "Paid"
    
    def remaining_display(self, obj):
        remaining = obj.remaining_amount
        color = '#e74c3c' if remaining > 0 else '#2ecc71'
        return format_html('<span style="color: {}; font-weight: bold;">${}</span>', color, "{:,.2f}".format(float(remaining)))
    remaining_display.short_description = "Remaining"
    
    def status_badge(self, obj):
        colors = {'unpaid': '#e74c3c', 'partial': '#f39c12', 'paid': '#2ecc71'}
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.get_status_display().upper()
        )
    status_badge.short_description = "Status"
    
    def actions_column(self, obj):
        pdf_url = f"/api/financial/invoices/{obj.pk}/pdf/"
        return format_html(
            '<a href="/admin/financial/invoice/{}/change/" class="button" style="padding: 4px 10px; margin-right: 5px; text-decoration: none;">Edit</a>'
            '<a href="{}" target="_blank" class="button" style="padding: 4px 10px; background: #3498db; color: white; border-radius: 4px; text-decoration: none;">Export PDF</a>',
            obj.pk, pdf_url
        )
    actions_column.short_description = "Actions"
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_id', 'invoice_number', 'client', 'project')
        }),
        ('Payment Details', {
            'fields': ('amount', 'amount_paid', 'invoice_date', 'status'),
            'description': 'Amount is auto-populated from project cost. Status auto-updates based on payments.'
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


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    form = PaymentForm
    list_display = ['payment_id', 'client_link', 'project_link', 'invoice_link', 'amount_display', 'remaining_from_invoice', 'payment_method_display', 'payment_date', 'transaction_reference']
    list_filter = ['payment_date', 'payment_method', 'client']
    search_fields = ['payment_id', 'invoice__invoice_number', 'client__name', 'transaction_reference']
    readonly_fields = ['payment_id', 'client', 'project', 'created_at', 'remaining_amount_display']
    raw_id_fields = ['invoice', 'created_by']
    list_per_page = 20
    date_hierarchy = 'payment_date'
    
    class Media:
        js = ('admin/js/payment_autofill.js',)
    
    def client_link(self, obj):
        return format_html('<a href="/admin/client_management/client/{}/change/">{}</a>', 
                          obj.client.id, obj.client.name)
    client_link.short_description = "Client"
    
    def project_link(self, obj):
        return format_html('<a href="/admin/client_management/project/{}/change/">{}</a>', 
                          obj.project.id, obj.project.name)
    project_link.short_description = "Project"
    
    def invoice_link(self, obj):
        return format_html('<a href="/admin/financial/invoice/{}/change/">{}</a>', 
                          obj.invoice.id, obj.invoice.invoice_number)
    invoice_link.short_description = "Invoice"
    
    def amount_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #2ecc71;">${}</span>', "{:,.2f}".format(float(obj.amount)))
    amount_display.short_description = "Amount"
    
    def remaining_from_invoice(self, obj):
        remaining = obj.invoice.remaining_amount if obj.invoice else 0
        color = '#e74c3c' if remaining > 0 else '#2ecc71'
        return format_html('<span style="color: {};">${}</span>', color, "{:,.2f}".format(float(remaining)))
    remaining_from_invoice.short_description = "Invoice Remaining"
    
    def remaining_amount_display(self, obj):
        if obj.invoice:
            remaining = obj.invoice.remaining_amount
            return format_html('<span>${} (Invoice: {})</span>', "{:,.2f}".format(float(remaining)), obj.invoice.invoice_number)
        return '-'
    remaining_amount_display.short_description = "Remaining from Invoice"
    
    def payment_method_display(self, obj):
        return obj.get_payment_method_display()
    payment_method_display.short_description = "Method"
    
    fieldsets = (
        ('Invoice Selection', {
            'fields': ('invoice', 'remaining_amount_display'),
            'description': 'Select an invoice - client and project will auto-populate. Amount will auto-fill to remaining balance.'
        }),
        ('Payment Details', {
            'fields': ('amount', 'payment_method', 'payment_date', 'transaction_reference')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Revenue)
class RevenueAdmin(ModelAdmin):
    list_display = ['revenue_id', 'client_link', 'project_link', 'amount_display', 'revenue_date', 'invoice_link']
    list_filter = ['revenue_date', 'client']
    search_fields = ['revenue_id', 'client__name', 'project__name']
    readonly_fields = ['revenue_id', 'created_at']
    raw_id_fields = ['client', 'project', 'invoice']
    
    def client_link(self, obj):
        return format_html('<a href="/admin/client_management/client/{}/change/">{}</a>', 
                          obj.client.id, obj.client.name)
    client_link.short_description = "Client"
    
    def project_link(self, obj):
        return format_html('<a href="/admin/client_management/project/{}/change/">{}</a>', 
                          obj.project.id, obj.project.name)
    project_link.short_description = "Project"
    
    def amount_display(self, obj):
        return format_html('<b>${}</b>', "{:,.2f}".format(float(obj.amount)))
    amount_display.short_description = "Amount"
    
    def invoice_link(self, obj):
        return format_html('<a href="/admin/financial/invoice/{}/change/">View Invoice</a>', obj.invoice.id)
    invoice_link.short_description = "Invoice"
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ClientBalance)
class ClientBalanceAdmin(ModelAdmin):
    list_display = ['client_link', 'total_paid_display', 'total_cost_display', 'pending_display', 'payment_percentage', 'last_updated']
    search_fields = ['client__name', 'client__email']
    raw_id_fields = ['client']
    readonly_fields = ['last_updated']
    
    def client_link(self, obj):
        return format_html('<a href="/admin/client_management/client/{}/change/"><strong>{}</strong></a>', 
                          obj.client.id, obj.client.name)
    client_link.short_description = "Client"
    
    def total_paid_display(self, obj):
        return format_html('<span style="color: #2ecc71; font-weight: bold;">${}</span>', "{:,.2f}".format(float(obj.total_invoiced)))
    total_paid_display.short_description = "Total Paid"
    
    def total_cost_display(self, obj):
        return format_html('<span>${}</span>', "{:,.2f}".format(float(obj.total_projects_cost)))
    total_cost_display.short_description = "Total Projects Cost"
    
    def pending_display(self, obj):
        color = '#e74c3c' if obj.pending_balance > 0 else '#2ecc71'
        return format_html('<span style="color: {}; font-weight: bold;">${}</span>', 
                          color, "{:,.2f}".format(float(obj.pending_balance)))
    pending_display.short_description = "Pending Balance"
    
    def payment_percentage(self, obj):
        if obj.total_projects_cost > 0:
            percentage = float((obj.total_invoiced / obj.total_projects_cost) * 100)
            return format_html('''
                <div style="width: 100px;">
                    <progress value="{}" max="100" style="width: 100%; height: 8px; border-radius: 4px;"></progress>
                    <br><small>{}% paid</small>
                </div>
            ''', percentage, "{:.1f}".format(percentage))
        return '0%'
    payment_percentage.short_description = "Payment %"
    
    fieldsets = (
        ('Client Information', {
            'fields': ('client',)
        }),
        ('Financial Summary', {
            'fields': ('opening_balance', 'total_projects_cost', 'total_invoiced', 'pending_balance'),
            'description': 'Pending Balance = Total Projects Cost - Total Paid'
        }),
        ('Credit Limit', {
            'fields': ('credit_limit',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False


@admin.register(CompanyRevenue)
class CompanyRevenueAdmin(ModelAdmin):
    list_display = ['date', 'total_revenue_display', 'expenses_display', 'net_profit_display', 'total_employees', 'total_clients', 'active_projects']
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['revenue_id', 'updated_at', 'total_clients', 'total_projects', 'active_projects', 'total_employees']
    
    def total_revenue_display(self, obj):
        return format_html('<span style="color: #2ecc71; font-weight: bold;">${}</span>', "{:,.2f}".format(float(obj.total_revenue)))
    total_revenue_display.short_description = "Revenue"
    
    def expenses_display(self, obj):
        return format_html('<span style="color: #e74c3c;">${}</span>', "{:,.2f}".format(float(obj.total_expenses)))
    expenses_display.short_description = "Expenses"
    
    def net_profit_display(self, obj):
        color = '#2ecc71' if obj.net_profit > 0 else '#e74c3c'
        return format_html('<span style="color: {}; font-weight: bold;">${}</span>', color, "{:,.2f}".format(float(obj.net_profit)))
    net_profit_display.short_description = "Net Profit"
    
    fieldsets = (
        ('Date Information', {
            'fields': ('date', 'revenue_id')
        }),
        ('Financial Summary', {
            'fields': ('total_revenue', 'total_expenses', 'net_profit'),
        }),
        ('Business Stats', {
            'fields': ('total_clients', 'total_projects', 'active_projects', 'total_employees'),
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False