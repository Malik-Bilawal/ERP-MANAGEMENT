from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class EmployeeRole(models.Model):
    """Roles for employees - e.g., Software Engineer, Designer, Manager"""
    
    role_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['role_name']
        verbose_name = "Employee Role"
        verbose_name_plural = "Employee Roles"
    
    def __str__(self):
        return self.role_name


class ExpenseCategory(models.Model):
    """Categories for company expenses - Medical, Bonus, Travel, etc."""
    
    EXPENSE_TYPES = [
        ('salary', 'Salary'),
        ('bonus', 'Bonus'),
        ('medical', 'Medical'),
        ('travel', 'Travel'),
        ('equipment', 'Equipment'),
        ('training', 'Training'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES, default='other')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"
    
    def __str__(self):
        return self.name


class MonthlyExpensePlan(models.Model):
    """Monthly expense plan - plan expenses before executing"""
    
    PLAN_STATUS = [
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    plan_id = models.CharField(max_length=20, unique=True, editable=False)
    month = models.DateField(help_text="Plan for month")
    
    # Planned amounts
    planned_salary = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    planned_bonus = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    planned_medical = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    planned_travel = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    planned_other = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    total_planned = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=PLAN_STATUS, default='draft')
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='expense_plans')
    
    class Meta:
        ordering = ['-month']
        verbose_name = "Monthly Expense Plan"
        verbose_name_plural = "Monthly Expense Plans"
        unique_together = ['month']
    
    def __str__(self):
        return f"Plan {self.month.strftime('%B %Y')} - ${self.total_planned}"
    
    def save(self, *args, **kwargs):
        if not self.plan_id:
            year = self.month.year
            count = MonthlyExpensePlan.objects.filter(month__year=year).count() + 1
            self.plan_id = f"EXP-PLAN-{year}-{count:04d}"
        
        self.total_planned = (
            self.planned_salary + 
            self.planned_bonus + 
            self.planned_medical + 
            self.planned_travel + 
            self.planned_other
        )
        super().save(*args, **kwargs)
    
    @property
    def actual_expenses(self):
        """Calculate actual expenses for this month"""
        from django.db.models import Sum
        from financial.models import Payment, Revenue
        from hr.models import SalaryPayment
        
        # Salary expenses
        salary_total = SalaryPayment.objects.filter(
            month__month=self.month.month,
            month__year=self.month.year,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return {
            'salary': salary_total,
            'bonus': Decimal('0.00'),  # Can be tracked separately
            'medical': Decimal('0.00'),
            'travel': Decimal('0.00'),
            'other': Decimal('0.00'),
            'total': salary_total
        }
    
    @property
    def remaining_budget(self):
        actual = self.actual_expenses['total']
        return self.total_planned - actual


class Employee(models.Model):
    """Employee with role and salary"""
    
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
    ]
    
    employee_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    role = models.ForeignKey(EmployeeRole, on_delete=models.PROTECT, related_name='employees')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='full_time')
    
    salary = models.DecimalField(max_digits=15, decimal_places=2, help_text="Monthly salary")
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    emergency_contact_name = models.CharField(max_length=200, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            year = timezone.now().year
            count = Employee.objects.filter(joining_date__year=year).count() + 1
            self.employee_id = f"EMP-{year}-{count:04d}"
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def total_salary_paid(self):
        return sum(p.amount for p in self.salary_payments.filter(status='completed'))
    
    @property
    def pending_salary(self):
        return self.salary - self.total_salary_paid


class SalaryPayment(models.Model):
    """Track salary payments to employees"""
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
    ]
    
    payment_id = models.CharField(max_length=20, unique=True, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_payments')
    
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    month = models.DateField(help_text="Salary for month")
    
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='bank_transfer')
    payment_date = models.DateField(blank=True, null=True)
    
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='salary_payments_recorded')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month', '-created_at']
        verbose_name = "Salary Payment"
        verbose_name_plural = "Salary Payments"
        indexes = [
            models.Index(fields=['payment_id']),
            models.Index(fields=['month']),
        ]
    
    def __str__(self):
        return f"{self.payment_id} - {self.employee.full_name} - {self.month.strftime('%B %Y')}"
    
    def save(self, *args, **kwargs):
        if not self.payment_id:
            year = timezone.now().year
            count = SalaryPayment.objects.filter(payment_date__year=year).count() + 1
            self.payment_id = f"SAL-{year}-{count:06d}"
        super().save(*args, **kwargs)


class SalaryRecord(models.Model):
    """Monthly salary record for each employee"""
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_records')
    month = models.DateField()
    
    base_salary = models.DecimalField(max_digits=15, decimal_places=2)
    bonus = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=15, decimal_places=2)
    
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month']
        verbose_name = "Salary Record"
        verbose_name_plural = "Salary Records"
        unique_together = ['employee', 'month']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.month.strftime('%B %Y')}"
    
    def save(self, *args, **kwargs):
        self.net_salary = self.base_salary + self.bonus - self.deductions
        super().save(*args, **kwargs)