# salary/models.py
from django.db import models
from django.core.validators import MinValueValidator
from staff.models import Staff
from projects.models import Project

class SalaryStructure(models.Model):
    """Defines salary components and structure"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Earnings Components
    basic_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=50,
        help_text="Percentage of basic salary"
    )
    hra_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=40,
        help_text="House Rent Allowance percentage"
    )
    conveyance_allowance = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Fixed conveyance allowance"
    )
    medical_allowance = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Fixed medical allowance"
    )
    special_allowance = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Special allowance"
    )
    
    # Deduction Components
    pf_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=12,
        help_text="Provident Fund percentage"
    )
    esi_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.75,
        help_text="ESI percentage"
    )
    professional_tax = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Professional tax amount"
    )
    tds_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="TDS percentage"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Salary Structure"
        verbose_name_plural = "Salary Structures"
    
    def __str__(self):
        return self.name

class SalaryAssignment(models.Model):
    """Assign salary structure to staff with effective dates"""
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='salary_assignments')
    salary_structure = models.ForeignKey(SalaryStructure, on_delete=models.PROTECT)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    custom_base_salary = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Override base salary if different from staff/role"
    )
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-effective_from']
        unique_together = ['staff', 'effective_from']
        verbose_name = "Salary Assignment"
        verbose_name_plural = "Salary Assignments"
    
    def __str__(self):
        return f"{self.staff} - {self.salary_structure}"

class SalarySlip(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='salary_slips')
    month = models.DateField(help_text="Month of salary (use first day of month)")
    salary_structure = models.ForeignKey(SalaryStructure, on_delete=models.PROTECT)
    
    # Earnings
    basic = models.DecimalField(max_digits=10, decimal_places=2)
    hra = models.DecimalField(max_digits=10, decimal_places=2)
    conveyance = models.DecimalField(max_digits=10, decimal_places=2)
    medical = models.DecimalField(max_digits=10, decimal_places=2)
    special = models.DecimalField(max_digits=10, decimal_places=2)
    overtime = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Deductions
    pf = models.DecimalField(max_digits=10, decimal_places=2)
    esi = models.DecimalField(max_digits=10, decimal_places=2)
    professional_tax = models.DecimalField(max_digits=10, decimal_places=2)
    tds = models.DecimalField(max_digits=10, decimal_places=2)
    loan_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Totals
    gross_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Attendance/Work details
    working_days = models.DecimalField(max_digits=5, decimal_places=2, default=30)
    days_present = models.DecimalField(max_digits=5, decimal_places=2)
    days_absent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    leave_taken = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-month', 'staff']
        unique_together = ['staff', 'month']
        verbose_name = "Salary Slip"
        verbose_name_plural = "Salary Slips"
    
    def __str__(self):
        return f"{self.staff} - {self.month.strftime('%B %Y')} - ₹{self.net_pay}"
    
    def calculate_net_pay(self):
        """Calculate net pay from earnings and deductions"""
        self.gross_earnings = sum([
            self.basic, self.hra, self.conveyance, 
            self.medical, self.special, self.overtime, 
            self.bonus, self.other_earnings
        ])
        self.total_deductions = sum([
            self.pf, self.esi, self.professional_tax,
            self.tds, self.loan_deduction, 
            self.advance_deduction, self.other_deductions
        ])
        self.net_pay = self.gross_earnings - self.total_deductions
        return self.net_pay
    
    def save(self, *args, **kwargs):
        self.calculate_net_pay()
        super().save(*args, **kwargs)

class StaffInvoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
# Change this line in StaffInvoice class
    invoice_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
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
        verbose_name = "Staff Invoice"
        verbose_name_plural = "Staff Invoices"
    
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
    
    class Meta:
        verbose_name = "Invoice Line Item"
        verbose_name_plural = "Invoice Line Items"
    
    def __str__(self):
        return self.description
    
    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)