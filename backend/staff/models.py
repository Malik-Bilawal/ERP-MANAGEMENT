# staff/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Role(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Base salary for this role"
    )
    hourly_rate = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Hourly rate for this role"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def staff_count(self):
        return self.staff_members.count()
class Staff(models.Model):
    EMPLOYMENT_TYPE = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
    ]
    
    PAYMENT_FREQUENCY = [
        ('monthly', 'Monthly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('weekly', 'Weekly'),
        ('hourly', 'Hourly'),
    ]
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Professional Information
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='staff_members')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE)
    payment_frequency = models.CharField(max_length=20, choices=PAYMENT_FREQUENCY, default='monthly')
    join_date = models.DateField(default=timezone.now)
    exit_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Salary Information
    base_salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Monthly/Annual base salary"
    )
    hourly_rate = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Hourly rate (for hourly employees)"
    )
    overtime_rate = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Overtime hourly rate (1.5x, 2x, etc.)"
    )
    
    # Bank Details
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    pan_number = models.CharField(max_length=20, blank=True)
    
    # Tax Information
    tax_id = models.CharField(max_length=50, blank=True, help_text="Tax ID / Social Security Number")
    tax_exemption = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Tax exemption amount"
    )
    
    # Leave Balances
    annual_leave_balance = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Annual leave days remaining"
    )
    sick_leave_balance = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Sick leave days remaining"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_staff'
    )
    
    class Meta:
        ordering = ['first_name', 'last_name']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'role']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def current_salary(self):
        """Get current salary based on role or individual setting"""
        if self.base_salary:
            return self.base_salary
        elif self.role and self.role.base_salary:
            return self.role.base_salary
        return 0
    
    @property
    def current_hourly_rate(self):
        """Get current hourly rate based on role or individual setting"""
        if self.hourly_rate:
            return self.hourly_rate
        elif self.role and self.role.hourly_rate:
            return self.role.hourly_rate
        return 0