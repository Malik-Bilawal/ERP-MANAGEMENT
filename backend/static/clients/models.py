from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Client(models.Model):
    client_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    total_revenue_generated = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'clients'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['company']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.company}"