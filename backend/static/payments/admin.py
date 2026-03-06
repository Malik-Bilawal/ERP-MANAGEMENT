from django.contrib import admin
from .models import Payment, Invoice

class InvoiceInline(admin.StackedInline):
    model = Invoice
    extra = 0
    readonly_fields = ['invoice_number', 'generated_date']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'client', 'project', 'amount', 'status', 'payment_date', 'due_date']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['client__name', 'project__project_name', 'transaction_reference']
    readonly_fields = ['payment_date', 'created_at', 'updated_at']
    inlines = [InvoiceInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('client', 'project', 'amount')
        }),
        ('Payment Details', {
            'fields': ('payment_date', 'due_date', 'status', 'payment_method', 'transaction_reference')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_as_completed']
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        for payment in queryset:
            if not hasattr(payment, 'invoice'):
                Invoice.objects.create(payment=payment)
    mark_as_completed.short_description = "Mark selected payments as completed"

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'payment', 'generated_date', 'is_sent', 'sent_date']
    list_filter = ['is_sent', 'generated_date']
    search_fields = ['invoice_number', 'payment__client__name']
    readonly_fields = ['invoice_number', 'generated_date']