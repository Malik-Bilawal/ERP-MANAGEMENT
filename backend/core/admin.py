# core/admin.py
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import CompanySettings

@admin.register(CompanySettings)
class CompanySettingsAdmin(ModelAdmin):
    list_display = ['company_name', 'email', 'phone', 'currency']
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'company_logo', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address',)
        }),
        ('Tax & Financial', {
            'fields': ('tax_number', 'fiscal_year_start', 'currency')
        }),
    )
    
    def has_add_permission(self, request):
        # Prevent adding multiple settings
        if CompanySettings.objects.exists():
            return False
        return super().has_add_permission(request)