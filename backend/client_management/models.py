# client_management/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator

User = get_user_model()

# Import SubService from services app
from services.models import SubService

class Client(models.Model):
    """Enhanced Client Model with Complete Information"""
    CLIENT_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('business', 'Business'),
        ('government', 'Government'),
        ('non_profit', 'Non-Profit'),
        ('startup', 'Startup'),
        ('enterprise', 'Enterprise'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('lead', 'Lead'),
        ('negotiation', 'In Negotiation'),
        ('past', 'Past Client'),
        ('blacklisted', 'Blacklisted'),
    ]
    
    # Basic Information
    client_id = models.CharField(max_length=20, unique=True, editable=False)
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPE_CHOICES, default='individual')
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Business Information
    company_name = models.CharField(max_length=200, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tax ID / GST")
    
    # Address Information
    billing_address = models.TextField()
    shipping_address = models.TextField(blank=True, null=True, verbose_name="Shipping Address")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Pakistan')
    postal_code = models.CharField(max_length=20)
    
    # Contact Persons
    primary_contact_name = models.CharField(max_length=100)
    primary_contact_designation = models.CharField(max_length=100, blank=True, null=True)
    secondary_contact_name = models.CharField(max_length=100, blank=True, null=True)
    secondary_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Financial Information
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    payment_terms = models.IntegerField(default=30, help_text="Payment terms in days")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Tax rate percentage")
    
    # Status and Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lead')
    source = models.CharField(max_length=100, blank=True, null=True, help_text="How did you find us?")
    notes = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_clients')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_clients')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client_id']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.client_id:
            # Generate unique client ID
            year = timezone.now().year
            count = Client.objects.filter(created_at__year=year).count() + 1
            self.client_id = f"CLT-{year}-{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.client_id} - {self.name}"
    
    @property
    def total_projects(self):
        return self.projects.count()
    
    @property
    def active_projects(self):
        return self.projects.filter(status='active').count()
    
    @property
    def total_revenue(self):
        # Will be updated when invoices are created
        return Decimal('0.00')
    
    @property
    def pending_payments(self):
        # Will be updated when invoices are created
        return Decimal('0.00')


class Project(models.Model):
    """Comprehensive Project Management"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('delayed', 'Delayed'),
    ]
    
    PROJECT_TYPE_CHOICES = [
        ('fixed', 'Fixed Price'),
        ('hourly', 'Hourly Billing'),
        ('retainer', 'Retainer'),
        ('milestone', 'Milestone Based'),
    ]
    
    # Basic Information
    project_id = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Project Details
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, default='fixed')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    
    # Financial Details
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="If hourly billing")
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, editable=False)
    
    # Timeline
    start_date = models.DateField()
    estimated_end_date = models.DateField()
    actual_end_date = models.DateField(null=True, blank=True)
    
    # Team
    project_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_projects')
    team_members = models.ManyToManyField(User, related_name='assigned_projects', blank=True)
    
    # Services and Tasks
    assigned_services = models.ManyToManyField(SubService, through='ProjectService', related_name='projects')
    
    # Progress Tracking
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    completion_notes = models.TextField(blank=True, null=True)
    
    # Additional
    tags = models.CharField(max_length=200, blank=True, null=True, help_text="Comma separated tags")
    notes = models.TextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project_id']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.project_id:
            year = timezone.now().year
            count = Project.objects.filter(created_at__year=year).count() + 1
            self.project_id = f"PRJ-{year}-{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.project_id} - {self.name}"
    
    @property
    def total_hours_worked(self):
        return self.time_entries.filter(is_billable=True).aggregate(
            total=models.Sum('hours')
        )['total'] or 0
    
    @property
    def total_billable_amount(self):
        if self.project_type == 'hourly':
            return self.total_hours_worked * self.hourly_rate
        return self.budget
    
    @property
    def days_remaining(self):
        if self.status == 'completed':
            return 0
        today = timezone.now().date()
        if today > self.estimated_end_date:
            return - (today - self.estimated_end_date).days
        return (self.estimated_end_date - today).days
    
    @property
    def is_overdue(self):
        return self.status not in ['completed', 'cancelled'] and timezone.now().date() > self.estimated_end_date


class ProjectService(models.Model):
    """Assign services to projects with custom pricing"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    sub_service = models.ForeignKey(SubService, on_delete=models.CASCADE)
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['project', 'sub_service']
    
    @property
    def total_price(self):
        price = self.custom_price if self.custom_price else self.sub_service.price
        return price * self.quantity


class TimeEntry(models.Model):
    """Track work hours for projects"""
    WORK_TYPE_CHOICES = [
        ('development', 'Development'),
        ('design', 'Design'),
        ('meeting', 'Meeting'),
        ('research', 'Research'),
        ('testing', 'Testing'),
        ('deployment', 'Deployment'),
        ('maintenance', 'Maintenance'),
        ('support', 'Support'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='time_entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_entries')
    date = models.DateField(default=timezone.now)
    hours = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    work_type = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES, default='development')
    description = models.TextField()
    is_billable = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_entries')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = "Time Entries"
    
    def __str__(self):
        return f"{self.project.name} - {self.user.username} - {self.hours}h"
    
    @property
    def billable_amount(self):
        if self.is_billable and self.project.project_type == 'hourly':
            return self.hours * self.project.hourly_rate
        return 0


class Milestone(models.Model):
    """Project milestones for milestone-based billing"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['due_date']
    
    def __str__(self):
        return f"{self.project.name} - {self.name}"


class ClientDocument(models.Model):
    """Store client-related documents"""
    DOCUMENT_TYPES = [
        ('contract', 'Contract'),
        ('proposal', 'Proposal'),
        ('agreement', 'Agreement'),
        ('nda', 'NDA'),
        ('invoice', 'Invoice'),
        ('receipt', 'Receipt'),
        ('other', 'Other'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='documents')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='client_documents/%Y/%m/')
    version = models.CharField(max_length=10, default='1.0')
    notes = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.client.name} - {self.title}"


class ClientCommunication(models.Model):
    """Track all communications with clients"""
    COMMUNICATION_TYPE = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('meeting', 'Meeting'),
        ('whatsapp', 'WhatsApp'),
        ('other', 'Other'),
    ]
    
    DIRECTION_CHOICES = [
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='communications')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='communications')
    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPE)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    conducted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='communications')
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.client.name} - {self.subject} ({self.date.strftime('%Y-%m-%d')})"