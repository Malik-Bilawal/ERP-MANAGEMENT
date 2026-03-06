from django.db import models
from django.core.validators import MinValueValidator
from clients.models import Client

class Project(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    project_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(
        Client, 
        on_delete=models.PROTECT,
        related_name='projects',
        db_column='client_id'
    )
    project_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0.00  # Add default value
    )
    actual_cost = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        default=0.00,  # Change default to 0 instead of null
        validators=[MinValueValidator(0)]
    )
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['client', 'status']),
        ]
    
    def __str__(self):
        return self.project_name
    
    @property
    def budget_variance(self):
        """Calculate variance between budgeted cost and actual cost"""
        # Handle None values by converting to 0
        cost_value = self.cost if self.cost is not None else 0
        actual_value = self.actual_cost if self.actual_cost is not None else 0
        return cost_value - actual_value
    
    @property
    def budget_variance_percentage(self):
        """Calculate variance percentage"""
        cost_value = self.cost if self.cost is not None else 0
        if cost_value > 0:
            actual_value = self.actual_cost if self.actual_cost is not None else 0
            return ((cost_value - actual_value) / cost_value) * 100
        return 0
    
    def save(self, *args, **kwargs):
        # Ensure actual_cost is never None
        if self.actual_cost is None:
            self.actual_cost = 0
        if self.cost is None:
            self.cost = 0
        super().save(*args, **kwargs)