from django.db import models
from django.core.validators import MinValueValidator
from clients.models import Client
from projects.models import Project

class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
    ]
    
    payment_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(
        Client, 
        on_delete=models.PROTECT,
        related_name='payments',
        db_column='client_id'
    )
    project = models.ForeignKey(
        Project, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        db_column='project_id'
    )
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    payment_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='bank_transfer')
    transaction_reference = models.CharField(max_length=100, unique=True, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['client', 'status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount}"

class Invoice(models.Model):
    invoice_id = models.AutoField(primary_key=True)
    invoice_number = models.CharField(max_length=50, unique=True)
    payment = models.OneToOneField(
        Payment, 
        on_delete=models.CASCADE,
        related_name='invoice'
    )
    generated_date = models.DateField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='invoices/', null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    sent_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-generated_date']
    
    def __str__(self):
        return self.invoice_number
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number: INV-YYYYMMDD-XXXX
            from datetime import datetime
            import random
            date_str = datetime.now().strftime('%Y%m%d')
            random_str = str(random.randint(1000, 9999))
            self.invoice_number = f"INV-{date_str}-{random_str}"
        super().save(*args, **kwargs)