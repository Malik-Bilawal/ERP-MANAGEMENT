from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
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
    """Monthly expense plan - auto-calculated from active employees and manually adjustable"""
    
    PLAN_STATUS = [
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    plan_id = models.CharField(max_length=20, unique=True, editable=False)
    month = models.DateField(help_text="First day of the plan month (e.g., 2024-01-01 for January 2024)")
    
    # Planned amounts - auto-calculated but manually adjustable
    planned_salary = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    planned_bonus = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    planned_medical = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    planned_travel = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    planned_equipment = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    planned_training = models.DecimalField(max_digits=15, decimal_places=2, default=0)
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
            self.planned_equipment +
            self.planned_training +
            self.planned_other
        )
        super().save(*args, **kwargs)
    
    def auto_calculate_salary(self):
        """Auto-calculate planned_salary from all active employees' salaries"""
        active_employees = Employee.objects.filter(is_active=True)
        total_salary = active_employees.aggregate(total=models.Sum('salary'))['total'] or Decimal('0.00')
        self.planned_salary = total_salary
        return total_salary
    
    @property
    def actual_expenses(self):
        """Calculate actual expenses for this month from SalaryPayments and ActualExpense records"""
        from django.db.models import Sum
        
        plan_month = self.month.month
        plan_year = self.month.year
        
        # Salary expenses
        salary_total = SalaryPayment.objects.filter(
            month__month=plan_month,
            month__year=plan_year,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Lazy import to avoid circular dependency
        ActualExpense = self.__class__.objects.model  # placeholder, will be overridden
        
        # Import ActualExpense at runtime to avoid circular imports
        from hr.models import ActualExpense as ActualExpenseModel
        
        bonus_total = ActualExpenseModel.objects.filter(
            expense_month=self.month,
            category__expense_type='bonus',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        medical_total = ActualExpenseModel.objects.filter(
            expense_month=self.month,
            category__expense_type='medical',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        travel_total = ActualExpenseModel.objects.filter(
            expense_month=self.month,
            category__expense_type='travel',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        other_total = ActualExpenseModel.objects.filter(
            expense_month=self.month,
            category__expense_type='other',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        equipment_total = ActualExpenseModel.objects.filter(
            expense_month=self.month,
            category__expense_type='equipment',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        training_total = ActualExpenseModel.objects.filter(
            expense_month=self.month,
            category__expense_type='training',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_all = salary_total + bonus_total + medical_total + travel_total + equipment_total + training_total + other_total
        
        return {
            'salary': salary_total,
            'bonus': bonus_total,
            'medical': medical_total,
            'travel': travel_total,
            'equipment': equipment_total,
            'training': training_total,
            'other': other_total,
            'total': total_all
        }
    
    @property
    def remaining_budget(self):
        actual = self.actual_expenses['total']
        return self.total_planned - actual
    
    @property
    def utilization_percentage(self):
        """Calculate budget utilization percentage"""
        if self.total_planned == 0:
            return Decimal('0.00')
        actual = self.actual_expenses['total']
        return (actual / self.total_planned) * 100


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
    
    salary = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Monthly base salary"
    )
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    # Bank details for salary payments
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    
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
            models.Index(fields=['is_active']),
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
    
    def get_unpaid_months(self):
        """Get list of months where salary is not yet paid"""
        from django.db.models import Q
        
        # Get all salary records for this employee
        all_records = self.salary_records.all().order_by('-month')
        unpaid = [r for r in all_records if not r.is_paid]
        return unpaid
    
    def get_salary_summary(self, year=None):
        """Get salary summary for a specific year or current year"""
        from django.db.models import Sum, Q
        
        if year is None:
            year = timezone.now().year
        
        records = self.salary_records.filter(month__year=year)
        payments = self.salary_payments.filter(
            month__year=year,
            status='completed'
        )
        
        total_earned = records.aggregate(total=Sum('net_salary'))['total'] or Decimal('0.00')
        total_paid = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return {
            'year': year,
            'total_earned': total_earned,
            'total_paid': total_paid,
            'pending': total_earned - total_paid,
            'records_count': records.count(),
            'payments_count': payments.count(),
        }


class SalaryRecord(models.Model):
    """Monthly salary record for each employee - auto-generated or manual"""
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_records')
    month = models.DateField(help_text="First day of the salary month (e.g., 2024-01-01 for January 2024)")
    
    base_salary = models.DecimalField(max_digits=15, decimal_places=2)
    bonus = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=15, decimal_places=2)
    
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(blank=True, null=True)
    
    # Link to actual payment if exists
    salary_payment = models.OneToOneField(
        'SalaryPayment', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='salary_record'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month', 'employee']
        verbose_name = "Salary Record"
        verbose_name_plural = "Salary Records"
        unique_together = ['employee', 'month']
        indexes = [
            models.Index(fields=['month']),
            models.Index(fields=['is_paid']),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.month.strftime('%B %Y')} - ${self.net_salary}"
    
    def save(self, *args, **kwargs):
        self.net_salary = self.base_salary + self.bonus - self.deductions
        super().save(*args, **kwargs)


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
    
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    month = models.DateField(help_text="First day of the salary month (e.g., 2024-01-01 for January 2024)")
    
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
            models.Index(fields=['status']),
        ]
        # Prevent duplicate payments for same employee + month
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'month'],
                condition=models.Q(status__in=['pending', 'processing', 'completed']),
                name='unique_active_payment_per_month'
            )
        ]
    
    def __str__(self):
        return f"{self.payment_id} - {self.employee.full_name} - {self.month.strftime('%B %Y')} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.payment_id:
            year = timezone.now().year
            count = SalaryPayment.objects.filter(created_at__year=year).count() + 1
            self.payment_id = f"SAL-{year}-{count:06d}"
        
        # Auto-set payment_date when status changes to completed
        if self.status == 'completed' and not self.payment_date:
            self.payment_date = timezone.now().date()
        
        super().save(*args, **kwargs)
        
        # Update linked salary record if exists
        if hasattr(self, 'salary_record'):
            record = self.salary_record
            record.is_paid = (self.status == 'completed')
            record.payment_date = self.payment_date
            record.save()
        
        # Update company revenue summary when payment is completed
        if self.status == 'completed' and self.payment_date:
            from financial.models import CompanyRevenue
            CompanyRevenue.update_daily(self.payment_date)
            CompanyRevenue.update_daily(timezone.now().date())


class ActualExpense(models.Model):
    """Track actual non-salary expenses against monthly plans"""
    
    EXPENSE_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    expense_id = models.CharField(max_length=20, unique=True, editable=False)
    expense_month = models.DateField(
        help_text="Month this expense belongs to (first day of month)"
    )
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
    
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=EXPENSE_STATUS, default='pending')
    expense_date = models.DateField(help_text="Actual date of expense")
    
    # Optional employee link
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='expenses'
    )
    
    receipt = models.FileField(upload_to='expense_receipts/', blank=True, null=True)
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='expenses_recorded')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
        verbose_name = "Actual Expense"
        verbose_name_plural = "Actual Expenses"
        indexes = [
            models.Index(fields=['expense_id']),
            models.Index(fields=['expense_month']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.expense_id} - {self.category.name} - {self.amount} - {self.expense_date.strftime('%Y-%m')}"
    
    def save(self, *args, **kwargs):
        if not self.expense_id:
            year = self.expense_date.year if self.expense_date else timezone.now().year
            count = ActualExpense.objects.filter(expense_date__year=year).count() + 1
            self.expense_id = f"EXP-{year}-{count:06d}"
        super().save(*args, **kwargs)
        
        # Update company revenue when expense is completed
        if self.status == 'completed' and self.expense_date:
            from financial.models import CompanyRevenue
            CompanyRevenue.update_daily(self.expense_date)
            CompanyRevenue.update_daily(timezone.now().date())
