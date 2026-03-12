from django.contrib import admin
from unfold.admin import ModelAdmin  # Import Unfold's version
from .models import Project

@admin.register(Project)
class ProjectAdmin(ModelAdmin):  # Use Unfold ModelAdmin here
    # Unfold specific options
    compressed_fields = True  # Makes the form more compact/professional
    warn_unsaved_form = True  # Prevents accidental data loss
    
    list_display = ['project_id', 'project_name', 'client', 'cost', 'status', 'priority', 'deadline']
    list_filter = ['status', 'priority', 'client']
    search_fields = ['project_name', 'client__name', 'client__company']
    readonly_fields = ['budget_variance', 'budget_variance_percentage', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('project_name', 'client', 'description'),
            'classes': ['tab'], # Unfold can turn these into tabs
        }),
        ('Financial Information', {
            'fields': ('cost', 'actual_cost', 'budget_variance', 'budget_variance_percentage')
        }),
        ('Timeline', {
            'fields': ('start_date', 'deadline', 'completion_date')
        }),
        ('Status', {
            'fields': ('status', 'priority', 'created_at', 'updated_at')
        }),
    )