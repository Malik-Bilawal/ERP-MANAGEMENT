from decimal import Decimal
from django.contrib import admin
from django.urls import reverse
from django.urls import path as url_path
from django.utils.html import format_html
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from unfold.admin import ModelAdmin, TabularInline
from .models import Invoice, InvoiceItem, Payment, ClientLedger, ClientBalance, Revenue, CompanyRevenue
from client_management.models import Client, Project


class PaymentInline(TabularInline):
    model = Payment
    extra = 0
    fields = ['payment_id', 'amount', 'payment_method', 'payment_date', 'transaction_reference']
    readonly_fields = ['payment_id']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ['invoice_id', 'client_link', 'project_link', 'amount_display', 'amount_paid_display', 'remaining_display', 'status_badge', 'invoice_date']
    list_filter = ['status', 'invoice_date', 'client']
    search_fields = ['invoice_id', 'invoice_number', 'client__name']
    readonly_fields = ['invoice_id', 'invoice_number', 'amount_paid', 'status', 'remaining_budget_display', 'created_at', 'created_by']
    list_per_page = 20
    inlines = [PaymentInline]

    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_id', 'invoice_number', 'client', 'project')
        }),
        ('Project Budget Info (Read-only)', {
            'fields': ('remaining_budget_display',),
            'classes': ('collapse',)
        }),
        ('Financial Details', {
            'fields': ('amount', 'amount_paid', 'status', 'invoice_date', 'due_date')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_option'),
        }),
        ('Additional', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    class Media:
        js = ('admin/js/invoice_form.js',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url_path('project-details/', self.admin_site.admin_view(self.project_details_view), name='invoice_project_details'),
            url_path('project-details/<int:project_id>/', self.admin_site.admin_view(self.project_details_view), name='invoice_project_details_by_id'),
        ]
        return custom_urls + urls

    def project_details_view(self, request, project_id=None):
        if project_id:
            try:
                project = Project.objects.get(pk=project_id)
                return JsonResponse({
                    'budget': str(project.budget),
                    'total_invoiced': str(project.total_invoiced),
                    'remaining_budget': str(project.remaining_budget),
                })
            except Project.DoesNotExist:
                return JsonResponse({'error': 'Project not found'}, status=404)

        client_id = request.GET.get('client_id')
        if not client_id:
            return JsonResponse({'error': 'client_id required'}, status=400)

        projects = Project.objects.filter(client_id=client_id)
        
        result = []
        for project in projects:
            if project.remaining_budget > 0:
                result.append({
                    'id': project.id,
                    'project_id': project.project_id,
                    'name': project.name,
                    'budget': str(project.remaining_budget),
                })
        
        return JsonResponse(result, safe=False)

    def remaining_budget_display(self, obj):
        if obj.project:
            project = obj.project
            return format_html(
                '<div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 16px;">'
                '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">'
                '<div><p style="margin: 0; font-size: 12px; color: #0369a1;">Total Budget</p>'
                '<p style="margin: 4px 0 0; font-size: 18px; font-weight: bold; color: #0c4a6e;">${}</p></div>'
                '<div><p style="margin: 0; font-size: 12px; color: #0369a1;">Already Invoiced</p>'
                '<p style="margin: 4px 0 0; font-size: 18px; font-weight: bold; color: #ea580c;">${}</p></div>'
                '<div><p style="margin: 0; font-size: 12px; color: #0369a1;">Remaining</p>'
                '<p style="margin: 4px 0 0; font-size: 18px; font-weight: bold; color: #16a34a;">${}</p></div>'
                '</div></div>',
                "{:,.2f}".format(float(project.budget)),
                "{:,.2f}".format(float(project.total_invoiced)),
                "{:,.2f}".format(float(project.remaining_budget)),
            )
        return format_html(
            '<div style="background: #fef3c7; border: 1px solid #fde68a; border-radius: 8px; padding: 12px;">'
            '<p style="margin: 0; color: #92400e;">Select a project to see budget information</p>'
            '</div>'
        )
    remaining_budget_display.short_description = "Project Budget Breakdown"

    def project_cost_display(self, obj):
        if obj.project:
            return format_html('<b>${}</b>', "{:,.2f}".format(float(obj.project.remaining_budget)))
        return format_html('<span style="color: #92400e;">Select a project to see remaining balance</span>')
    project_cost_display.short_description = "Project Remaining Balance"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
            obj.payment_method = request.POST.get('payment_method', 'bank_transfer')

        super().save_model(request, obj, form, change)

        if not change and obj.amount > 0:
            payment_option = request.POST.get('payment_option', 'full')
            
            if payment_option == 'full':
                Payment.objects.create(
                    invoice=obj,
                    client=obj.client,
                    project=obj.project,
                    amount=obj.amount,
                    payment_method=obj.payment_method,
                    payment_date=obj.invoice_date,
                    created_by=request.user,
                )

    def client_link(self, obj):
        if obj.client:
            url = reverse('admin:client_management_client_change', args=[obj.client.id])
            return format_html('<a href="{}">{}</a>', url, obj.client.name)
        return "-"
    client_link.short_description = "Client"

    def project_link(self, obj):
        if obj.project:
            url = reverse('admin:client_management_project_change', args=[obj.project.id])
            return format_html('<a href="{}">{}</a>', url, obj.project.name)
        return "-"
    project_link.short_description = "Project"

    def amount_display(self, obj):
        return format_html('<span style="font-weight: bold;">${}</span>', "{:,.2f}".format(float(obj.amount or 0)))
    amount_display.short_description = "Total Amount"

    def amount_paid_display(self, obj):
        return format_html('<span style="color: #2ecc71;">${}</span>', "{:,.2f}".format(float(obj.amount_paid or 0)))
    amount_paid_display.short_description = "Paid"

    def remaining_display(self, obj):
        remaining = (obj.amount or Decimal('0.00')) - (obj.amount_paid or Decimal('0.00'))
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


from django import forms

@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ['payment_id', 'client_link', 'invoice_link', 'amount_display', 'payment_method_display', 'payment_date']
    list_filter = ['payment_date', 'payment_method', 'client']
    search_fields = ['payment_id', 'invoice__invoice_number', 'client__name', 'transaction_reference']
    readonly_fields = ['payment_id', 'client', 'project', 'created_at', 'created_by']
    raw_id_fields = ['invoice']
    list_per_page = 20
    date_hierarchy = 'payment_date'

    def client_link(self, obj):
        if obj.client:
            url = reverse('admin:client_management_client_change', args=[obj.client.id])
            return format_html('<a href="{}">{}</a>', url, obj.client.name)
        return "-"
    client_link.short_description = "Client"

    def invoice_link(self, obj):
        if obj.invoice:
            url = reverse('admin:financial_invoice_change', args=[obj.invoice.id])
            return format_html('<a href="{}">{}</a>', url, obj.invoice.invoice_number)
        return "-"
    invoice_link.short_description = "Invoice"

    def amount_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #2ecc71;">${}</span>', "{:,.2f}".format(float(obj.amount)))
    amount_display.short_description = "Amount"

    def payment_method_display(self, obj):
        return obj.get_payment_method_display()
    payment_method_display.short_description = "Method"

    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'invoice', 'client', 'project')
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


@admin.register(ClientLedger)
class ClientLedgerAdmin(ModelAdmin):
    list_display = ['client_link', 'transaction_type_badge', 'description', 'debit_display', 'credit_display', 'running_balance_display', 'transaction_date']
    list_filter = ['transaction_type', 'transaction_date', 'client']
    search_fields = ['client__name', 'description']
    readonly_fields = ['client', 'project', 'invoice', 'payment', 'transaction_type', 'description', 'debit', 'credit', 'running_balance', 'transaction_date', 'created_at']
    list_per_page = 50

    def client_link(self, obj):
        if obj.client:
            url = reverse('admin:client_management_client_change', args=[obj.client.id])
            return format_html('<a href="{}">{}</a>', url, obj.client.name)
        return "-"
    client_link.short_description = "Client"

    def transaction_type_badge(self, obj):
        colors = {'invoice': '#3498db', 'payment': '#2ecc71', 'credit_note': '#e67e22', 'adjustment': '#9b59b6'}
        color = colors.get(obj.transaction_type, '#95a5a6')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.get_transaction_type_display()
        )
    transaction_type_badge.short_description = "Type"

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

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ClientBalance)
class ClientBalanceAdmin(ModelAdmin):
    list_display = ['client_link', 'total_cost_display', 'total_paid_display', 'pending_display', 'payment_percentage', 'last_updated']
    search_fields = ['client__name', 'client__email']
    raw_id_fields = ['client']
    readonly_fields = ['total_projects_cost', 'total_paid', 'pending_balance', 'last_updated']

    def client_link(self, obj):
        if obj.client:
            url = reverse('admin:client_management_client_change', args=[obj.client.id])
            return format_html('<a href="{}"><strong>{}</strong></a>', url, obj.client.name)
        return "-"
    client_link.short_description = "Client"

    def total_cost_display(self, obj):
        return format_html('<span>${}</span>', "{:,.2f}".format(float(obj.total_projects_cost)))
    total_cost_display.short_description = "Total Cost"

    def total_paid_display(self, obj):
        return format_html('<span style="color: #2ecc71; font-weight: bold;">${}</span>', "{:,.2f}".format(float(obj.total_paid)))
    total_paid_display.short_description = "Total Paid"

    def pending_display(self, obj):
        color = '#e74c3c' if obj.pending_balance > 0 else '#2ecc71'
        return format_html('<span style="color: {}; font-weight: bold;">${}</span>', color, "{:,.2f}".format(float(obj.pending_balance)))
    pending_display.short_description = "Pending"

    def payment_percentage(self, obj):
        if obj.total_projects_cost > 0:
            percentage = float((obj.total_paid / obj.total_projects_cost) * 100)
            return format_html('''
                <div style="width: 100px;">
                    <progress value="{}" max="100" style="width: 100%; height: 8px; border-radius: 4px;"></progress>
                    <br><small>{}% paid</small>
                </div>
            ''', percentage, "{:.1f}".format(percentage))
        return '0%'
    payment_percentage.short_description = "Payment %"

    def has_add_permission(self, request):
        return False


@admin.register(Revenue)
class RevenueAdmin(ModelAdmin):
    list_display = ['revenue_id', 'client_link', 'amount_display', 'revenue_date', 'invoice_link']
    list_filter = ['revenue_date', 'client']
    search_fields = ['revenue_id', 'client__name']
    readonly_fields = ['revenue_id', 'client', 'project', 'invoice', 'amount', 'revenue_date', 'description', 'created_at']

    def client_link(self, obj):
        if obj.client:
            url = reverse('admin:client_management_client_change', args=[obj.client.id])
            return format_html('<a href="{}">{}</a>', url, obj.client.name)
        return "-"
    client_link.short_description = "Client"

    def amount_display(self, obj):
        return format_html('<b>${}</b>', "{:,.2f}".format(float(obj.amount)))
    amount_display.short_description = "Amount"

    def invoice_link(self, obj):
        if obj.invoice:
            url = reverse('admin:financial_invoice_change', args=[obj.invoice.id])
            return format_html('<a href="{}">View</a>', url)
        return "-"
    invoice_link.short_description = "Invoice"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
