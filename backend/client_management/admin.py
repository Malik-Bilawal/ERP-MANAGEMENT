from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from rangefilter.filters import DateRangeFilter
from import_export.admin import ImportExportModelAdmin
from .models import (
    Client, Project, ProjectService, TimeEntry, 
    Milestone, ClientDocument, ClientCommunication
)

@admin.register(Client)
class ClientAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ['client_id', 'name', 'email', 'phone', 'client_type', 'status', 'total_projects', 'total_revenue_display', 'created_at']
    list_filter = ['status', 'client_type', 'source', 'created_at']
    search_fields = ['client_id', 'name', 'email', 'phone', 'company_name']
    list_editable = ['status']
    list_per_page = 20
    raw_id_fields = ['created_by', 'assigned_to']
    
    fieldsets = (
        ('Client Identification', {
            'fields': ('client_id', 'client_type', 'name', 'email', 'phone', 'alternative_phone')
        }),
        ('Business Information', {
            'fields': ('company_name', 'website', 'industry', 'tax_id')
        }),
        ('Address Information', {
            'fields': ('billing_address', 'shipping_address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Contact Persons', {
            'fields': ('primary_contact_name', 'primary_contact_designation', 'secondary_contact_name', 'secondary_contact_phone')
        }),
        ('Financial Information', {
            'fields': ('credit_limit', 'payment_terms', 'tax_rate')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'source', 'assigned_to', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['client_id', 'created_at', 'updated_at']
    
    def total_revenue_display(self, obj):
     return format_html('<b>${}</b>', "{:,.2f}".format(obj.total_revenue))
    total_revenue_display.short_description = "Total Revenue"
    
    def total_projects(self, obj):
        return obj.total_projects
    total_projects.short_description = "Projects"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ['project_id', 'name', 'client', 'project_type', 'status', 'priority', 'budget', 'progress_percentage_display', 'days_remaining']
    list_filter = ['status', 'priority', 'project_type', 'start_date', ('estimated_end_date', DateRangeFilter)]
    search_fields = ['project_id', 'name', 'client__name', 'client__email']
    list_editable = ['status', 'priority']
    list_per_page = 20
    raw_id_fields = ['client', 'project_manager', 'created_by']
    filter_horizontal = ['team_members']
    
    def progress_percentage_display(self, obj):
        return format_html('<div style="width: 100px;"><progress value="{}" max="100" style="width: 100%;"></progress> {}%</div>', 
                          obj.progress_percentage, obj.progress_percentage)
    progress_percentage_display.short_description = "Progress"
    
    def days_remaining(self, obj):
        days = obj.days_remaining
        if days < 0:
            return format_html('<span style="color: red;">{} days overdue</span>', abs(days))
        elif days == 0:
            return format_html('<span style="color: orange;">Due today</span>')
        else:
            return format_html('<span style="color: green;">{} days</span>', days)
    days_remaining.short_description = "Remaining"
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('project_id', 'client', 'name', 'description', 'project_type')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Financial Details', {
            'fields': ('budget', 'hourly_rate', 'total_cost')
        }),
        ('Timeline', {
            'fields': ('start_date', 'estimated_end_date', 'actual_end_date')
        }),
        ('Team Management', {
            'fields': ('project_manager', 'team_members')
        }),
        ('Progress Tracking', {
            'fields': ('progress_percentage', 'completion_notes')
        }),
        ('Additional Information', {
            'fields': ('tags', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['project_id', 'total_cost', 'created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProjectService)
class ProjectServiceAdmin(ModelAdmin):
    list_display = ['project', 'sub_service', 'quantity', 'total_price_display', 'created_at']
    list_filter = ['project__status', 'sub_service__service__service_category']
    search_fields = ['project__name', 'sub_service__name', 'sub_service__code']
    raw_id_fields = ['project', 'sub_service']
    
    def total_price_display(self, obj):
     return format_html('${}', "{:,.2f}".format(obj.total_price))
    total_price_display.short_description = "Total Price"


@admin.register(TimeEntry)
class TimeEntryAdmin(ModelAdmin):
    list_display = ['project', 'user', 'date', 'hours', 'work_type', 'is_billable', 'is_approved', 'billable_amount_display']
    list_filter = ['date', 'work_type', 'is_billable', 'is_approved', 'user']
    search_fields = ['project__name', 'description', 'user__username']
    list_editable = ['is_approved']
    raw_id_fields = ['project', 'user', 'approved_by']
    
    def billable_amount_display(self, obj):
     if obj.is_billable:
        return format_html('${}', "{:,.2f}".format(obj.billable_amount))
     return '-'
    billable_amount_display.short_description = "Billable Amount"
    
    fieldsets = (
        ('Entry Details', {
            'fields': ('project', 'user', 'date', 'hours', 'work_type', 'description')
        }),
        ('Billing', {
            'fields': ('is_billable',)
        }),
        ('Approval', {
            'fields': ('is_approved', 'approved_by', 'approved_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if obj.is_approved and not obj.approved_at:
            obj.approved_by = request.user
            obj.approved_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(Milestone)
class MilestoneAdmin(ModelAdmin):
    list_display = ['project', 'name', 'due_date', 'amount', 'status', 'completed_date']
    list_filter = ['status', 'due_date']
    search_fields = ['project__name', 'name']
    list_editable = ['status']
    raw_id_fields = ['project']


@admin.register(ClientDocument)
class ClientDocumentAdmin(ModelAdmin):
    list_display = ['client', 'document_type', 'title', 'version', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['client__name', 'title']
    raw_id_fields = ['client', 'project', 'uploaded_by']


@admin.register(ClientCommunication)
class ClientCommunicationAdmin(ModelAdmin):
    list_display = ['client', 'communication_type', 'direction', 'subject', 'date', 'conducted_by', 'follow_up_date']
    list_filter = ['communication_type', 'direction', 'date', 'follow_up_date']
    search_fields = ['client__name', 'subject', 'content']
    raw_id_fields = ['client', 'project', 'conducted_by']