from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from rangefilter.filters import DateRangeFilter

from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from .models import Client

class ClientResource(resources.ModelResource):
    class Meta:
        model = Client
        fields = ('client_id', 'name', 'company', 'email', 'total_revenue_generated', 'created_at')

@admin.register(Client)
# --- 2. ADD ModelAdmin HERE FIRST ---
class ClientAdmin(ModelAdmin, ImportExportModelAdmin):
    resource_class = ClientResource
    
    # --- 3. ADD THESE TO FIX IMPORT/EXPORT BUTTON STYLES ---
    import_form_class = ImportForm
    export_form_class = ExportForm
    # -------------------------------------------------------
    
    list_display = ['client_id', 'name', 'company', 'email', 'total_revenue_display', 'project_count', 'is_active_display']
    
    # --- 4. SWAP DateRangeFilter FOR Unfold's RangeDateFilter ---
    list_filter = ['is_active', 'company', ('created_at', RangeDateFilter)]
    
    search_fields = ['name', 'company', 'email']
    list_per_page = 25
    save_on_top = True
    
    # --- YOUR CUSTOM METHODS STAY EXACTLY THE SAME ---
    def total_revenue_display(self, obj):
        color_class = 'text-green-600 dark:text-green-400' if obj.total_revenue_generated > 10000 else 'text-orange-500 dark:text-orange-400'
        revenue = float(obj.total_revenue_generated) if obj.total_revenue_generated else 0
        return mark_safe(
            f'<span class="font-semibold {color_class}">${revenue:,.2f}</span>'
        )
    total_revenue_display.short_description = 'Revenue'
    total_revenue_display.admin_order_field = 'total_revenue_generated'
    
    def project_count(self, obj):
        count = obj.projects.count()
        return format_html(
            '<span class="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-1 rounded-full dark:bg-blue-900 dark:text-blue-300 border border-blue-400">{} Projects</span>',
            count
        )
    project_count.short_description = 'Projects'
    
    def is_active_display(self, obj):
        if obj.is_active:
            return mark_safe('<span class="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-1 rounded-full dark:bg-green-900 dark:text-green-300 border border-green-400">Active</span>')
        return mark_safe('<span class="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-1 rounded-full dark:bg-red-900 dark:text-red-300 border border-red-400">Inactive</span>')
    is_active_display.short_description = 'Status'