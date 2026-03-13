from django.contrib import admin
from django import forms
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import Assignment
from staff.models import Staff, Role
from projects.models import Project

class AssignmentAdminForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = '__all__'
        widgets = {
            'responsibilities': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['staff'].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name} - {obj.role}"
        self.fields['project'].label_from_instance = lambda obj: f"{obj.project_name} ({obj.client})"
        self.fields['role'].label_from_instance = lambda obj: obj.name

@admin.register(Assignment)
class AssignmentAdmin(ModelAdmin):
    form = AssignmentAdminForm
    change_list_template = "admin/assignments/assignment/change_list.html"
    
    list_display = [
        'id',
        'staff_info',
        'project_info',
        'role_info',
        'assigned_date',  # This is fine for list display
        'status_badge',
        'priority_badge',
        'progress',
        'is_overdue_badge',
    ]
    
    list_filter = [
        'status',
        'priority',
        'is_active',
        'assigned_date',  # This is fine for list filter
        'project__client',
        'role',
    ]
    
    search_fields = [
        'staff__first_name',
        'staff__last_name',
        'staff__email',
        'project__project_name',
        'role__name',
        'responsibilities',
    ]
    
    autocomplete_fields = ['staff', 'project', 'role']
    
    # READONLY FIELDS - Add assigned_date here since it's auto_now_add
    readonly_fields = ['assigned_date', 'created_at', 'updated_at', 'hours_worked']
    
    # FIELDSETS - REMOVE assigned_date from here
    fieldsets = (
        ('Assignment Details', {
            'fields': (
                'staff',
                'project',
                'role',
                # 'assigned_date',  <-- REMOVE THIS LINE
            ),
            'description': 'Select staff member, project, and role'
        }),
        ('Timeline', {
            'fields': (
                'start_date',
                'end_date',
            ),
            'classes': ('collapse',),
        }),
        ('Work Allocation', {
            'fields': (
                'hours_allocated',
                'hours_worked',
                ('priority', 'status'),
                'is_active',
            ),
        }),
        ('Responsibilities & Notes', {
            'fields': (
                'responsibilities',
                'notes',
            ),
            'classes': ('wide',),
        }),
        ('System Information', {
            'fields': (
                'assigned_date',  # <-- MOVE IT HERE (optional, since it's readonly)
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    list_fullwidth = True
    list_filter_submit_button = True
    warn_unsaved_form = True
    compressed_fields = True
    
    @display(description="Staff", ordering="staff__first_name")
    def staff_info(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}"
    
    @display(description="Project", ordering="project__project_name")
    def project_info(self, obj):
        return obj.project.project_name
    
    @display(description="Role", ordering="role__name")
    def role_info(self, obj):
        return obj.role.name if obj.role else "-"
    
    @display(description="Status")
    def status_badge(self, obj):
        return obj.status
    
    @display(description="Priority")
    def priority_badge(self, obj):
        return obj.priority
    
    @display(description="Progress")
    def progress(self, obj):
        return f"{obj.progress_percentage}%"
    
    @display(description="Overdue")
    def is_overdue_badge(self, obj):
        if obj.is_overdue:
            return "⚠️ Overdue"
        return "✓ On Track"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'staff',
            'staff__role',
            'project',
            'project__client',
            'role'
        )