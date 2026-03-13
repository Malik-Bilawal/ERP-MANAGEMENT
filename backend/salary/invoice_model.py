# salary/invoice_models.py (or create a new app called 'invoices')
from django.db import models
from staff.models import Staff
from projects.models import Project

class StaffInvoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='invoices')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Invoice Details
    invoice_date = models.DateField()
    due_date = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Financial Details
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Work Details
    hours_worked = models.DecimalField(max_digits=8, decimal_places=2)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    
    # Payment Details
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-invoice_date']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.staff}"
    
    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.status != 'paid' and self.due_date < timezone.now().date():
            return True
        return False

class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(StaffInvoice, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return self.description
    
    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)