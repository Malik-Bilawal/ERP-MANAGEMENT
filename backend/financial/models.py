from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from client_management.models import Client, Project

User = get_user_model()


class Invoice(models.Model):
    """Invoice for client projects with automatic status tracking"""

    STATUS_CHOICES = [
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
    ]

    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
        ('card', 'Credit/Debit Card'),
        ('other', 'Other'),
    ]

    PAYMENT_OPTIONS = [
        ('full', 'Full Payment'),
        ('partial', 'Partial Payment'),
    ]

    invoice_id = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, related_name='invoices')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')

    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)

    amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Total invoice amount")
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    payment_option = models.CharField(max_length=20, choices=PAYMENT_OPTIONS, default='full', help_text="Payment type: full or partial")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='paid')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='bank_transfer')

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')

    class Meta:
        ordering = ['-invoice_date']
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

    def save(self, *args, **kwargs):
        if not self.invoice_id:
            year = timezone.now().year
            last = Invoice.objects.filter(invoice_id__startswith=f"INV-{year}-").order_by('-invoice_id').first()
            if last:
                last_num = int(last.invoice_id.split('-')[-1])
                count = last_num + 1
            else:
                count = 1
            self.invoice_id = f"INV-{year}-{count:06d}"

        if not self.invoice_number:
            self.invoice_number = self.invoice_id

        if not self.amount and self.project:
            self.amount = self.project.budget

        super().save(*args, **kwargs)

        self._update_status()

    def _update_status(self):
        if self.amount_paid >= self.amount and self.amount > 0:
            new_status = 'paid'
        else:
            new_status = 'partial'

        if new_status != self.status:
            self.status = new_status
            Invoice.objects.filter(pk=self.pk).update(status=new_status)

    @property
    def remaining_amount(self):
        return max(self.amount - self.amount_paid, Decimal('0.00'))

    def __str__(self):
        client_name = self.client.name if self.client else "Unknown"
        return f"{self.invoice_id} - {client_name} - ${self.amount} ({self.get_status_display()})"


class InvoiceItem(models.Model):
    """Line items on an invoice"""

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    class Meta:
        ordering = ['id']
        verbose_name = "Invoice Item"
        verbose_name_plural = "Invoice Items"

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} - ${self.total}"


class Payment(models.Model):
    """Individual payment recorded against an invoice"""

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
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, related_name='payments')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='payments')

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='bank_transfer')
    payment_date = models.DateField(default=timezone.now)
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
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

        if self.invoice:
            self.client = self.invoice.client
            self.project = self.invoice.project

        super().save(*args, **kwargs)

        self._update_invoice()
        self._update_client_balance()

    def _update_invoice(self):
        total_paid = self.invoice.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        self.invoice.amount_paid = total_paid
        self.invoice.save(update_fields=['amount_paid'])
        self.invoice._update_status()

    def _update_client_balance(self):
        if not self.client:
            return
        balance, _ = ClientBalance.objects.get_or_create(client=self.client)
        balance.recalculate()

    def __str__(self):
        client_name = self.client.name if self.client else "Unknown"
        return f"{self.payment_id} - ${self.amount} - {client_name}"


class ClientLedger(models.Model):
    """Per-client transaction ledger with running balance"""

    TRANSACTION_TYPES = [
        ('invoice', 'Invoice Created'),
        ('payment', 'Payment Received'),
        ('credit_note', 'Credit Note'),
        ('adjustment', 'Manual Adjustment'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='ledger_entries')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')

    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)

    debit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), help_text="Amount owed (invoice)")
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), help_text="Amount paid (payment)")

    running_balance = models.DecimalField(max_digits=15, decimal_places=2, help_text="Pending balance after this entry")

    transaction_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['transaction_date', 'created_at']
        verbose_name = "Client Ledger Entry"
        verbose_name_plural = "Client Ledger Entries"
        indexes = [
            models.Index(fields=['client', 'transaction_date']),
            models.Index(fields=['client', 'transaction_type']),
        ]

    def __str__(self):
        return f"{self.client.name} - {self.description} - ${self.debit or self.credit}"


class ClientBalance(models.Model):
    """Client balance summary - auto-calculated from ledger"""

    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='balance')
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_projects_cost = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    pending_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Client Balances"

    def recalculate(self):
        # Only count projects that have invoices for billing purposes
        total_cost = Invoice.objects.filter(client=self.client).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        total_paid = Payment.objects.filter(client=self.client).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

        self.total_projects_cost = total_cost
        self.total_paid = total_paid
        self.pending_balance = total_cost - total_paid
        self.save()

    def __str__(self):
        return f"{self.client.name} - Paid: ${self.total_paid} | Pending: ${self.pending_balance}"


class Revenue(models.Model):
    """Revenue records auto-created from payments"""

    revenue_id = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, related_name='revenues')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='revenues')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, related_name='revenues')
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
        client_name = self.client.name if self.client else "Unknown"
        return f"{self.revenue_id} - {client_name} - ${self.amount}"


class CompanyRevenue(models.Model):
    """Daily company revenue summary"""

    revenue_id = models.CharField(max_length=20, unique=True, editable=False)
    date = models.DateField(unique=True)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_profit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_clients = models.IntegerField(default=0)
    total_projects = models.IntegerField(default=0)
    active_projects = models.IntegerField(default=0)
    total_employees = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company Revenue"
        verbose_name_plural = "Company Revenues"
        ordering = ['-date']

    def save(self, *args, **kwargs):
        if not self.revenue_id:
            year = self.date.year
            count = CompanyRevenue.objects.filter(date__year=year).count() + 1
            self.revenue_id = f"REV-{year}-{count:06d}"
        super().save(*args, **kwargs)

    @classmethod
    def update_daily(cls, date=None):
        from hr.models import Employee, SalaryPayment, ActualExpense

        if not date:
            date = timezone.now().date()

        total_revenue = Revenue.objects.filter(revenue_date=date).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        salary_expenses = SalaryPayment.objects.filter(status='completed', payment_date=date).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        other_expenses = ActualExpense.objects.filter(status='completed', expense_date=date).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        total_expenses = salary_expenses + other_expenses
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

@receiver(models.signals.post_save, sender=Payment)
def create_revenue_and_ledger_on_payment(sender, instance, created, **kwargs):
    if created:
        Revenue.objects.create(
            invoice=instance.invoice,
            client=instance.client,
            project=instance.project,
            amount=instance.amount,
            revenue_date=instance.payment_date,
            description=f"Payment {instance.payment_id} for Invoice {instance.invoice.invoice_id}"
        )

        if instance.client:
            # Recalculate client balance first
            balance, _ = ClientBalance.objects.get_or_create(client=instance.client)
            balance.recalculate()
            
            # The running_balance should be the balance AFTER this payment
            running_bal = balance.pending_balance

            ClientLedger.objects.create(
                client=instance.client,
                project=instance.project,
                invoice=instance.invoice,
                payment=instance,
                transaction_type='payment',
                description=f"Payment {instance.payment_id} - {instance.get_payment_method_display()}",
                credit=instance.amount,
                running_balance=running_bal,
                transaction_date=instance.payment_date,
            )

            # Recalculate client balance after payment is added
            balance, _ = ClientBalance.objects.get_or_create(client=instance.client)
            balance.recalculate()

        CompanyRevenue.update_daily(instance.payment_date)


@receiver(models.signals.post_delete, sender=Payment)
def cleanup_on_payment_delete(sender, instance, **kwargs):
    Revenue.objects.filter(
        description__startswith=f"Payment {instance.payment_id}"
    ).delete()

    ClientLedger.objects.filter(payment=instance).delete()

    if instance.invoice:
        total_paid = instance.invoice.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        instance.invoice.amount_paid = total_paid
        instance.invoice.save(update_fields=['amount_paid'])
        instance.invoice._update_status()

    if instance.client:
        balance, _ = ClientBalance.objects.get_or_create(client=instance.client)
        balance.recalculate()

    CompanyRevenue.update_daily(instance.payment_date)


@receiver(models.signals.post_save, sender=Invoice)
def update_ledger_on_invoice(sender, instance, created, **kwargs):
    if not instance.client:
        return
    
    balance, _ = ClientBalance.objects.get_or_create(client=instance.client)
    balance.recalculate()
    
    if created:
        # Get the current total invoiced BEFORE adding this new invoice
        existing_total = Invoice.objects.exclude(pk=instance.pk).filter(client=instance.client).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        paid = Payment.objects.filter(client=instance.client).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        # Pending balance BEFORE this new invoice
        balance_before = existing_total - paid
        
        ClientLedger.objects.filter(invoice=instance, transaction_type='invoice').delete()
        ClientLedger.objects.create(
            client=instance.client,
            project=instance.project,
            invoice=instance,
            transaction_type='invoice',
            description=f"Invoice {instance.invoice_id} created",
            debit=instance.amount,
            running_balance=balance_before + instance.amount,  # Balance AFTER this invoice
            transaction_date=instance.invoice_date,
        )
    else:
        # Update existing invoice ledger entry when invoice is edited
        ledger_entry = ClientLedger.objects.filter(invoice=instance, transaction_type='invoice').first()
        if ledger_entry:
            if ledger_entry.debit != instance.amount:
                # Recalculate all entries after this invoice
                ledger_entry.debit = instance.amount
                ledger_entry.running_balance = balance.pending_balance
                ledger_entry.save()


@receiver(models.signals.post_delete, sender=Invoice)
def cleanup_on_invoice_delete(sender, instance, **kwargs):
    invoice_pk = instance.pk
    client_id = instance.client_id
    
    # Delete all ledger entries for this invoice
    ClientLedger.objects.filter(invoice_id=invoice_pk).delete()
    
    # Delete all payments for this invoice  
    Payment.objects.filter(invoice_id=invoice_pk).delete()
    
    # Delete all revenue records for this invoice
    Revenue.objects.filter(invoice_id=invoice_pk).delete()

    # Recalculate balance AFTER deletion is complete
    if client_id:
        balance = ClientBalance.objects.filter(client_id=client_id).first()
        if balance:
            balance.recalculate()


@receiver(models.signals.post_save, sender=Project)
def update_balance_on_project(sender, instance, created, **kwargs):
    if instance.client:
        balance, _ = ClientBalance.objects.get_or_create(client=instance.client)
        balance.recalculate()
        CompanyRevenue.update_daily()


@receiver(models.signals.post_save, sender=Revenue)
def update_company_on_revenue(sender, instance, created, **kwargs):
    if created:
        CompanyRevenue.update_daily(instance.revenue_date)


try:
    from hr.models import SalaryPayment

    @receiver(models.signals.post_save, sender=SalaryPayment)
    def update_on_salary_payment(sender, instance, created, **kwargs):
        if created and instance.status == 'completed':
            if instance.payment_date:
                CompanyRevenue.update_daily(instance.payment_date)
            CompanyRevenue.update_daily(timezone.now().date())
except ImportError:
    pass
