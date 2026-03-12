from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action
from .models import Payment, Invoice

class InvoiceInline(TabularInline):
    model = Invoice
    extra = 0
    readonly_fields = ['invoice_number', 'generated_date']
    tab = True # Unfold: Displays as a separate tab

@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = [
        'payment_id', 
        'client', 
        'project', 
        'amount', 
        'status', 
        'payment_date', 
        'due_date'
    ]
    
    # Reverted to standard Django strings to bypass the (admin.E115) error
    list_filter = ['status', 'payment_method', 'payment_date']
    
    search_fields = ['client__name', 'project__project_name', 'transaction_reference']
    readonly_fields = ['payment_date', 'created_at', 'updated_at']
    inlines = [InvoiceInline]
    
    # Modern Layout Configuration
    fieldsets = (
        ('Basic Information', {
            'classes': ['tab'],
            'fields': ('client', 'project', 'amount'),
        }),
        ('Payment Details', {
            'classes': ['tab'],
            # Tuples inside here put fields on the same line (Modern Grid)
            'fields': (
                ('payment_date', 'due_date'), 
                ('status', 'payment_method'), 
                'transaction_reference'
            ),
        }),
        ('Additional Info', {
            'classes': ['collapse'],
            'fields': ('notes', 'created_at', 'updated_at'),
        }),
    )
    
    @action(description="Mark selected as completed")
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        for payment in queryset:
            if not hasattr(payment, 'invoice'):
                Invoice.objects.create(payment=payment)
        self.message_user(request, "Status updated successfully.")

@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ['invoice_number', 'payment', 'generated_date', 'is_sent', 'sent_date']
    list_filter = ['is_sent', 'generated_date']
    search_fields = ['invoice_number', 'payment__client__name']
    readonly_fields = ['invoice_number', 'generated_date']
    
    fieldsets = (
        (None, {
            'fields': (
                ('invoice_number', 'payment'), 
                ('is_sent', 'sent_date'), 
                'generated_date'
            )
        }),
    )