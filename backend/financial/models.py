from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from client_management.models import Client, Project
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum

User = get_user_model()

class Invoice(models.Model):
    """Invoice - Can be partial or full payment"""
    
    STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
    ]
    
    # Basic Information
    invoice_id = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invoices')
    
    # Invoice Details
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField(default=timezone.now)
    
    # Financial Details
    amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Invoice amount (can be partial payment)")
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Total amount paid against this invoice")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    
    class Meta:
        ordering = ['-invoice_date']
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
    
    def save(self, *args, **kwargs):
        # Auto-generate invoice ID if not exists
        if not self.invoice_id:
            year = timezone.now().year
            count = Invoice.objects.filter(invoice_date__year=year).count() + 1
            self.invoice_id = f"INV-{year}-{count:06d}"
        
        # Auto-generate invoice number if not exists
        if not self.invoice_number:
            self.invoice_number = self.invoice_id
        
        # Auto-populate amount from project if not set
        if not self.amount and self.project:
            self.amount = self.project.budget
        
        super().save(*args, **kwargs)
        
        # Update invoice status based on payments
        self._update_status()
    
    def _update_status(self):
        """Update invoice status based on amount paid"""
        if self.amount_paid >= self.amount:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        else:
            self.status = 'unpaid'
        Invoice.objects.filter(pk=self.pk).update(status=self.status, amount_paid=self.amount_paid)
    
    @property
    def remaining_amount(self):
        return self.amount - self.amount_paid
    
    def __str__(self):
        return f"{self.invoice_id} - {self.client.name} - ${self.amount} ({self.get_status_display()})"


class Payment(models.Model):
    """Individual payment against an invoice - tracks each payment separately"""
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
        ('card', 'Credit/Debit Card'),
        ('other', 'Other'),
    ]
    
    payment_id = models.CharField(max_length=20, unique=True, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='payments')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='bank_transfer')
    payment_date = models.DateField(default=timezone.now)
    transaction_reference = models.CharField(max_length=100, blank=True, null=True, help_text="Bank transaction ID, cheque number, etc.")
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_payments')
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
    
    def save(self, *args, **kwargs):
        if not self.payment_id:
            year = timezone.now().year
            count = Payment.objects.filter(payment_date__year=year).count() + 1
            self.payment_id = f"PAY-{year}-{count:06d}"
        
        # Ensure client and project match invoice
        if self.invoice:
            self.client = self.invoice.client
            self.project = self.invoice.project
        
        super().save(*args, **kwargs)
        
        # Update invoice amount_paid and status
        self._update_invoice()
        
        # Create revenue record
        self._create_revenue()
        
        # Update client balance
        self._update_client_balance()
        
        # Update company revenue
        CompanyRevenue.update_daily(self.payment_date)
    
    def _update_invoice(self):
        """Update the invoice's paid amount and status"""
        invoice = self.invoice
        total_paid = invoice.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        invoice.amount_paid = total_paid
        
        if total_paid >= invoice.amount:
            invoice.status = 'paid'
        elif total_paid > 0:
            invoice.status = 'partial'
        else:
            invoice.status = 'unpaid'
        
        invoice.save(update_fields=['amount_paid', 'status'])
    
    def _create_revenue(self):
        """Create revenue record for this payment"""
        Revenue.objects.create(
            invoice=self.invoice,
            client=self.client,
            project=self.project,
            amount=self.amount,
            revenue_date=self.payment_date,
            description=f"Payment {self.payment_id} for Invoice {self.invoice.invoice_id}"
        )
    
    def _update_client_balance(self):
        """Update client's pending balance"""
        client_balance, created = ClientBalance.objects.get_or_create(
            client=self.client,
            defaults={'opening_balance': Decimal('0.00')}
        )
        
        # Total paid by client
        total_paid = Payment.objects.filter(
            client=self.client
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Total project costs
        total_projects_cost = Project.objects.filter(
            client=self.client
        ).aggregate(total=Sum('budget'))['total'] or Decimal('0.00')
        
        client_balance.total_invoiced = total_paid
        client_balance.total_projects_cost = total_projects_cost
        client_balance.pending_balance = total_projects_cost - total_paid
        client_balance.save()
    
    def __str__(self):
        return f"{self.payment_id} - ${self.amount} - {self.client.name}"


class Revenue(models.Model):
    """Revenue Tracking - Auto-created from invoices"""
    revenue_id = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='revenues')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='revenues')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='revenues')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    revenue_date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-revenue_date']
        verbose_name_plural = "Revenues"
    
    def save(self, *args, **kwargs):
        if not self.revenue_id:
            year = timezone.now().year
            count = Revenue.objects.filter(revenue_date__year=year).count() + 1
            self.revenue_id = f"REV-{year}-{count:06d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.revenue_id} - {self.client.name} - ${self.amount}"


class ClientBalance(models.Model):
    """Client Balance Tracking - Shows pending payments"""
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='balance')
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_invoiced = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Total amount paid by client")
    total_projects_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Total cost of all projects")
    pending_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Amount client still owes")
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Client Balances"
    
    def __str__(self):
        return f"{self.client.name} - Paid: ${self.total_invoiced} | Pending: ${self.pending_balance}"


class CompanyRevenue(models.Model):
    """Overall Company Revenue Tracking"""
    revenue_id = models.CharField(max_length=20, unique=True, editable=False)
    date = models.DateField(unique=True)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Total expenses (salary, etc)")
    net_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Revenue - Expenses")
    total_clients = models.IntegerField(default=0)
    total_projects = models.IntegerField(default=0)
    active_projects = models.IntegerField(default=0)
    total_employees = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Company Revenue"
        verbose_name_plural = "Company Revenues"
        ordering = ['-date']
        ordering = ['-date']
    
    def save(self, *args, **kwargs):
        if not self.revenue_id:
            year = self.date.year
            count = CompanyRevenue.objects.filter(date__year=year).count() + 1
            self.revenue_id = f"REV-{year}-{count:06d}"
        super().save(*args, **kwargs)
    
    @classmethod
    def update_daily(cls, date=None):
        """Update daily revenue summary"""
        from hr.models import Employee, SalaryPayment
        
        if not date:
            date = timezone.now().date()
        
        # Total revenue for the day
        total_revenue = Revenue.objects.filter(
            revenue_date=date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Total salary expenses for the day
        total_expenses = SalaryPayment.objects.filter(
            status='completed',
            payment_date=date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Net profit
        net_profit = total_revenue - total_expenses
        
        summary, created = cls.objects.update_or_create(
            date=date,
            defaults={
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'net_profit': net_profit,
                'total_clients': Client.objects.filter(status='active').count(),
                'total_projects': Project.objects.count(),
                'active_projects': Project.objects.filter(status='in_progress').count(),
                'total_employees': Employee.objects.filter(is_active=True).count(),
            }
        )
        return summary
    
    def __str__(self):
        return f"{self.date} - Revenue: ${self.total_revenue}"


# ========== SIGNALS ==========
# These must be module level, not inside any class

@receiver(post_save, sender=Invoice)
def update_invoice_status_on_save(sender, instance, created, **kwargs):
    """Update invoice status when payments change"""
    instance._update_status()


@receiver(post_save, sender=Payment)
def update_on_payment(sender, instance, created, **kwargs):
    """Update balances when payment is created"""
    if created:
        # Update company revenue for the payment date
        CompanyRevenue.update_daily(instance.payment_date)
        
        # Also update for today if different
        today = timezone.now().date()
        if today != instance.payment_date:
            CompanyRevenue.update_daily(today)


# Import HR signals at the end to avoid circular imports
try:
    from hr.models import SalaryPayment
    
    @receiver(post_save, sender=SalaryPayment)
    def update_on_salary_payment(sender, instance, created, **kwargs):
        """Update company expenses when salary is paid"""
        if created and instance.status == 'completed':
            # Update company revenue for the payment date
            if instance.payment_date:
                CompanyRevenue.update_daily(instance.payment_date)
            
            # Also update for today
            today = timezone.now().date()
            CompanyRevenue.update_daily(today)
except ImportError:
    pass


@receiver(post_delete, sender=Payment)
def update_on_payment_delete(sender, instance, **kwargs):
    """Update balances when payment is deleted"""
    # Update client balance
    client_balance, _ = ClientBalance.objects.get_or_create(
        client=instance.client,
        defaults={'opening_balance': Decimal('0.00')}
    )
    
    # Recalculate totals
    total_paid = Payment.objects.filter(
        client=instance.client
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_projects_cost = Project.objects.filter(
        client=instance.client
    ).aggregate(total=Sum('budget'))['total'] or Decimal('0.00')
    
    client_balance.total_invoiced = total_paid
    client_balance.total_projects_cost = total_projects_cost
    client_balance.pending_balance = total_projects_cost - total_paid
    client_balance.save()
    
    # Update company revenue for the payment date
    CompanyRevenue.update_daily(instance.payment_date)


@receiver(post_save, sender=Project)
def update_client_balance_on_project(sender, instance, created, **kwargs):
    """Update client balance when project is created or updated"""
    if created or instance.budget:
        client_balance, _ = ClientBalance.objects.get_or_create(
            client=instance.client,
            defaults={'opening_balance': Decimal('0.00')}
        )
        
        total_projects_cost = Project.objects.filter(
            client=instance.client
        ).aggregate(total=Sum('budget'))['total'] or Decimal('0.00')
        
        total_paid = Payment.objects.filter(
            client=instance.client
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        client_balance.total_projects_cost = total_projects_cost
        client_balance.total_invoiced = total_paid
        client_balance.pending_balance = total_projects_cost - total_paid
        client_balance.save()
        
        CompanyRevenue.update_daily()


@receiver(post_delete, sender=Invoice)
def update_on_invoice_delete(sender, instance, **kwargs):
    """Update balances when invoice is deleted"""
    client_balance, _ = ClientBalance.objects.get_or_create(
        client=instance.client,
        defaults={'opening_balance': Decimal('0.00')}
    )
    
    total_paid = Payment.objects.filter(
        client=instance.client
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_projects_cost = Project.objects.filter(
        client=instance.client
    ).aggregate(total=Sum('budget'))['total'] or Decimal('0.00')
    
    client_balance.total_invoiced = total_paid
    client_balance.total_projects_cost = total_projects_cost
    client_balance.pending_balance = total_projects_cost - total_paid
    client_balance.save()
    
    CompanyRevenue.update_daily(instance.invoice_date)
    
    # Also update for today if different
    today = timezone.now().date()
    if today != instance.invoice_date:
        CompanyRevenue.update_daily(today)


@receiver(post_save, sender=Revenue)
def update_company_revenue_on_revenue(sender, instance, created, **kwargs):
    """Auto-update company revenue when revenue is created"""
    CompanyRevenue.update_daily(instance.revenue_date)


@receiver(post_save, sender=Project)
def update_client_balance_on_project(sender, instance, created, **kwargs):
    """Update client balance when project is created or updated"""
    if created or instance.budget:
        # Update client balance
        client_balance, _ = ClientBalance.objects.get_or_create(
            client=instance.client,
            defaults={'opening_balance': Decimal('0.00')}
        )
        
        # Recalculate total projects cost for this client
        total_projects_cost = Project.objects.filter(
            client=instance.client
        ).aggregate(total=Sum('budget'))['total'] or Decimal('0.00')
        
        # Recalculate total paid for this client
        total_paid = Invoice.objects.filter(
            client=instance.client
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        client_balance.total_projects_cost = total_projects_cost
        client_balance.total_invoiced = total_paid
        client_balance.pending_balance = total_projects_cost - total_paid
        client_balance.save()
        
        # Update company revenue
        CompanyRevenue.update_daily()


@receiver(post_delete, sender=Invoice)
def update_on_invoice_delete(sender, instance, **kwargs):
    """Update balances when invoice is deleted"""
    # Update client balance
    client_balance, _ = ClientBalance.objects.get_or_create(
        client=instance.client,
        defaults={'opening_balance': Decimal('0.00')}
    )
    
    # Recalculate totals
    total_paid = Invoice.objects.filter(
        client=instance.client
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_projects_cost = Project.objects.filter(
        client=instance.client
    ).aggregate(total=Sum('budget'))['total'] or Decimal('0.00')
    
    client_balance.total_invoiced = total_paid
    client_balance.total_projects_cost = total_projects_cost
    client_balance.pending_balance = total_projects_cost - total_paid
    client_balance.save()
    
    # Update company revenue for the invoice date
    CompanyRevenue.update_daily(instance.invoice_date)