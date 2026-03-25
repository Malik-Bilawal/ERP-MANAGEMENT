from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from rangefilter.filters import DateRangeFilter
from import_export.admin import ImportExportModelAdmin
from django.contrib.auth import get_user_model
from .models import (
    ServiceCategory, Service, SubService, ClientService, 
    ServicePricingHistory, ServiceCategoryAnalytics
)

User = get_user_model()

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ['id', 'name', 'icon_display', 'is_active', 'total_sub_services', 'total_clients', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']  # Only fields in list_display can be editable
    list_per_page = 20
    
    def icon_display(self, obj):
        if obj.icon:
            return format_html('<i class="{}" style="font-size: 20px;"></i>', obj.icon)
        return "-"
    icon_display.short_description = "Icon"
    
    def total_sub_services(self, obj):
        return obj.total_sub_services
    total_sub_services.short_description = "Sub-Services"
    
    def total_clients(self, obj):
        return obj.total_clients_using
    total_clients.short_description = "Clients"
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Visual Settings', {
            'fields': ('icon', 'color_code'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Service)
class ServiceAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ['id', 'service_category', 'name', 'base_price', 'is_active', 'total_sub_services']
    list_filter = ['service_category', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'service_category__name']
    list_editable = ['base_price', 'is_active']  # Both fields are in list_display
    list_per_page = 20
    raw_id_fields = ['service_category']
    
    def total_sub_services(self, obj):
        return obj.total_sub_services
    total_sub_services.short_description = "Sub-Services"
    
    fieldsets = (
        ('Service Information', {
            'fields': ('service_category', 'name', 'description', 'base_price', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SubService)
class SubServiceAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ['id', 'service', 'name', 'code', 'price_display', 'estimated_duration_days', 'is_active']
    list_filter = ['service__service_category', 'service', 'is_active', 'requires_approval']
    search_fields = ['name', 'code', 'description', 'service__name']
    list_editable = ['estimated_duration_days', 'is_active'] 
    list_per_page = 20
    raw_id_fields = ['service']
    
    def price_display(self, obj):
     formatted_price = "{:,.2f}".format(obj.price)
     return format_html('<b>${}</b>', formatted_price)
     price_display.short_description = "Price"
    
    fieldsets = (
        ('Sub-Service Information', {
            'fields': ('service', 'name', 'description', 'code', 'is_active')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'estimated_duration_days', 'requires_approval')
        }),
        ('Metadata', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        else:
            # Track price changes
            old_obj = SubService.objects.filter(pk=obj.pk).first()
            if old_obj and old_obj.price != obj.price:
                ServicePricingHistory.objects.create(
                    sub_service=obj,
                    old_price=old_obj.price,
                    new_price=obj.price,
                    changed_by=request.user,
                    reason="Price updated via admin"
                )
        super().save_model(request, obj, form, change)


@admin.register(ClientService)
class ClientServiceAdmin(ModelAdmin):
    list_display = ['id', 'client', 'sub_service', 'final_price_display', 'status', 'assigned_to', 'start_date', 'end_date']
    list_filter = ['status', 'assigned_to', ('start_date', DateRangeFilter), ('end_date', DateRangeFilter)]
    search_fields = ['client__name', 'client__email', 'sub_service__name', 'sub_service__code']
    list_editable = ['status']  # Only status is editable
    list_per_page = 20
    raw_id_fields = ['client', 'sub_service', 'assigned_to']
    readonly_fields = ['created_at', 'updated_at']
    
    def final_price_display(self, obj):
        price = obj.final_price
        if obj.custom_price:
            return format_html('<b>${:,.2f}</b> <span style="color: green;">(Custom)</span>', price)
        return format_html('${:,.2f}', price)
    final_price_display.short_description = "Price"
    
    fieldsets = (
        ('Client & Service', {
            'fields': ('client', 'sub_service', 'assigned_to', 'status')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Pricing', {
            'fields': ('custom_price',),
            'description': 'Leave custom price blank to use standard service price'
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ServicePricingHistory)
class ServicePricingHistoryAdmin(ModelAdmin):
    list_display = ['sub_service', 'old_price', 'new_price', 'changed_by', 'changed_at']
    list_filter = ['changed_at', 'changed_by']
    search_fields = ['sub_service__name', 'sub_service__code', 'reason']
    readonly_fields = ['sub_service', 'old_price', 'new_price', 'changed_by', 'changed_at', 'reason']
    list_per_page = 20
    raw_id_fields = ['sub_service', 'changed_by']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ServiceCategoryAnalytics)
class ServiceCategoryAnalyticsAdmin(ModelAdmin):
    list_display = ['service_category', 'month', 'total_revenue', 'total_clients', 'total_projects']
    list_filter = ['service_category', ('month', DateRangeFilter)]
    search_fields = ['service_category__name']
    readonly_fields = ['created_at']
    list_per_page = 20
    raw_id_fields = ['service_category']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False