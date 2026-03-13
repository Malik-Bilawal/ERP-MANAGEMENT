# In assignments/models.py
from django.db import models
from staff.models import Staff, Role  # Import Role
from projects.models import Project

class Assignment(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='assignments')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='staff_assignments')
    # Change this line - make it a ForeignKey to Role
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='assignments')
    assigned_date = models.DateField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    # Remove the old role_in_project field
    # role_in_project = models.CharField(max_length=100)  # REMOVE THIS LINE
    
    responsibilities = models.TextField(blank=True, help_text="Specific responsibilities for this project")
    hours_allocated = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Total hours allocated")
    hours_worked = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Hours worked so far")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['staff', 'project', 'is_active']
        ordering = ['-assigned_date', 'project']
        indexes = [
            models.Index(fields=['staff', 'is_active']),
            models.Index(fields=['project', 'is_active']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.staff} → {self.project} ({self.role.name if self.role else 'No Role'})"
    
    @property
    def progress_percentage(self):
        """Calculate progress based on hours worked vs allocated"""
        if self.hours_allocated and self.hours_allocated > 0:
            return min(round((self.hours_worked / self.hours_allocated) * 100), 100)
        return 0
    
    @property
    def is_overdue(self):
        """Check if assignment is overdue"""
        from django.utils import timezone
        if self.end_date and self.status != 'completed' and self.end_date < timezone.now().date():
            return True
        return False