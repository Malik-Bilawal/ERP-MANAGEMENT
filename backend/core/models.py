# core/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CompanySettings(models.Model):
    """Company-wide settings"""
    company_name = models.CharField(max_length=200, default="SRF IMS")
    company_logo = models.ImageField(upload_to='company/', blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    fiscal_year_start = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Company Setting"
        verbose_name_plural = "Company Settings"
    
    def __str__(self):
        return self.company_name
    
    def save(self, *args, **kwargs):
        # Ensure only one settings record exists
        if not self.pk and CompanySettings.objects.exists():
            raise ValueError("Only one CompanySettings instance allowed")
        super().save(*args, **kwargs)