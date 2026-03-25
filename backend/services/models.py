# services/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

class ServiceCategory(models.Model):
    """Main service categories like Web Development, Graphic Design, etc."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Service Category Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="FontAwesome icon class", verbose_name="Icon")
    color_code = models.CharField(max_length=7, blank=True, null=True, help_text="Hex color code", verbose_name="Color Code")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_service_categories')
    
    class Meta:
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def total_sub_services(self):
        """Get total number of sub-services in this category"""
        return self.services.filter(is_active=True).count()
    
    @property
    def total_clients_using(self):
        """Get total number of clients using services from this category"""
        from client_management.models import Client
        return Client.objects.filter(client_services__sub_service__service__service_category=self).distinct().count()

class Service(models.Model):
    """Main services under categories"""
    service_category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services', verbose_name="Service Category")
    name = models.CharField(max_length=100, verbose_name="Service Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Base Price")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_services')
    
    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['service_category', 'name']
        unique_together = ['service_category', 'name']
    
    def __str__(self):
        return f"{self.service_category.name} - {self.name}"
    
    @property
    def total_sub_services(self):
        """Get total number of sub-services under this service"""
        return self.sub_services.filter(is_active=True).count()

class SubService(models.Model):
    """Detailed sub-services like E-commerce Development, Blog Website, etc."""
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='sub_services', verbose_name="Main Service")
    name = models.CharField(max_length=100, verbose_name="Sub-Service Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    code = models.CharField(max_length=50, unique=True, verbose_name="Service Code", 
                           help_text="Unique code for this sub-service (e.g., WEB-ECOMM, GRAPH-BRAND)")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Standard Price")
    estimated_duration_days = models.PositiveIntegerField(default=7, verbose_name="Estimated Duration (Days)")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    requires_approval = models.BooleanField(default=False, verbose_name="Requires Approval")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sub_services')
    
    class Meta:
        verbose_name = "Sub-Service"
        verbose_name_plural = "Sub-Services"
        ordering = ['service__service_category', 'service', 'name']
        unique_together = ['service', 'code']
    
    def __str__(self):
        return f"{self.service.name} - {self.name} ({self.code})"
    
    def save(self, *args, **kwargs):
        if not self.code:
            # Auto-generate code if not provided
            category_prefix = self.service.service_category.name[:3].upper()
            service_prefix = self.service.name[:3].upper()
            import random
            random_num = random.randint(100, 999)
            self.code = f"{category_prefix}-{service_prefix}-{random_num}"
        super().save(*args, **kwargs)
    
    @property
    def formatted_price(self):
        """Return formatted price with currency"""
        return f"${self.price:,.2f}"

# services/models.py - Update the ClientService model
class ClientService(models.Model):
    """Track which services a client has subscribed to or purchased"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Change this line from 'core.Client' to 'client_management.Client'
    client = models.ForeignKey('client_management.Client', on_delete=models.CASCADE, related_name='client_services', verbose_name="Client")
    sub_service = models.ForeignKey(SubService, on_delete=models.CASCADE, related_name='client_services', verbose_name="Sub-Service")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_services', verbose_name="Assigned To")
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Custom Price")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_client_services')
    
    class Meta:
        verbose_name = "Client Service"
        verbose_name_plural = "Client Services"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.client} - {self.sub_service}"
    
    @property
    def final_price(self):
        """Get final price (custom if set, else standard)"""
        return self.custom_price if self.custom_price else self.sub_service.price
    
    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = timezone.now().date()
        super().save(*args, **kwargs)

class ServicePricingHistory(models.Model):
    """Track pricing changes for services"""
    sub_service = models.ForeignKey(SubService, on_delete=models.CASCADE, related_name='pricing_history', verbose_name="Sub-Service")
    old_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Old Price")
    new_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="New Price")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='price_changes', verbose_name="Changed By")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Changed At")
    reason = models.TextField(blank=True, null=True, verbose_name="Reason for Change")
    
    class Meta:
        verbose_name = "Service Pricing History"
        verbose_name_plural = "Service Pricing Histories"
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.sub_service} - ${self.old_price} → ${self.new_price}"

class ServiceCategoryAnalytics(models.Model):
    """Analytics for service categories"""
    service_category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='analytics', verbose_name="Service Category")
    month = models.DateField(verbose_name="Month")
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Total Revenue")
    total_clients = models.PositiveIntegerField(default=0, verbose_name="Total Clients")
    total_projects = models.PositiveIntegerField(default=0, verbose_name="Total Projects")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Service Category Analytics"
        verbose_name_plural = "Service Category Analytics"
        ordering = ['service_category', '-month']
        unique_together = ['service_category', 'month']
    
    def __str__(self):
        return f"{self.service_category.name} - {self.month.strftime('%B %Y')}"