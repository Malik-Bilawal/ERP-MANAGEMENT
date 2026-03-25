from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from client_management.models import Client, Project
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

User = get_user_model()

class Invoice(models.Model):
    """Simple Invoice - Auto-captures project cost"""
    
    # Basic Information
    invoice_id = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='invoices')
    
    # Invoice Details
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField(default=timezone.now)
    
    # Financial Details - Auto-populated from project
    amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Auto-populated from project cost")
    
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
        
        # After saving, update client balance and create revenue
        self._update_client_balance()
        self._create_revenue()
    
    def _update_client_balance(self):
        """Update client's pending balance"""
        client_balance, created = ClientBalance.objects.get_or_create(
            client=self.client,
            defaults={
                'opening_balance': Decimal('0.00')
            }
        )
        
        # Calculate total paid amount (sum of all invoices for this client)
        total_paid = Invoice.objects.filter(
            client=self.client
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate total project costs (sum of all projects for this client)
        total_projects_cost = Project.objects.filter(
            client=self.client
        ).aggregate(total=models.Sum('budget'))['total'] or Decimal('0.00')
        
        # Pending balance = Total Projects Cost - Total Paid
        client_balance.total_invoiced = total_paid
        client_balance.total_projects_cost = total_projects_cost
        client_balance.pending_balance = total_projects_cost - total_paid
        client_balance.save()
    
    def _create_revenue(self):
        """Auto-create revenue record"""
        Revenue.objects.get_or_create(
            invoice=self,
            defaults={
                'client': self.client,
                'project': self.project,
                'amount': self.amount,
                'revenue_date': self.invoice_date,
                'description': f"Payment received for {self.project.name}"
            }
        )
    
    def __str__(self):
        return f"{self.invoice_id} - {self.client.name} - ${self.amount}"


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
    total_clients = models.IntegerField(default=0)
    total_projects = models.IntegerField(default=0)
    active_projects = models.IntegerField(default=0)
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
        """Update daily revenue summary"""
        if not date:
            date = timezone.now().date()
        
        total_revenue = Revenue.objects.filter(
            revenue_date=date
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        summary, created = cls.objects.update_or_create(
            date=date,
            defaults={
                'total_revenue': total_revenue,
                'total_clients': Client.objects.filter(status='active').count(),
                'total_projects': Project.objects.count(),
                'active_projects': Project.objects.filter(status='in_progress').count(),
            }
        )
        return summary
    
    def __str__(self):
        return f"{self.date} - Revenue: ${self.total_revenue}"