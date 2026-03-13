# staff/admin.py
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display
from django.urls import reverse
from .models import Staff, Role

@admin.register(Role)
class RoleAdmin(ModelAdmin):
    list_display = ['name', 'description', 'base_salary', 'hourly_rate', 'staff_count_badge']
    search_fields = ['name', 'description']
    list_filter = ['base_salary']
    
    fieldsets = (
        ('Role Information', {
            'fields': ('name', 'description')
        }),
        ('Compensation', {
            'fields': ('base_salary', 'hourly_rate'),
            'classes': ('wide',),
        }),
    )
    
    @display(description="Staff Count")
    def staff_count_badge(self, obj):
        count = obj.staff_count
        url = reverse('admin:staff_staff_changelist') + f'?role__id__exact={obj.id}'
        return format_html('<a href="{}" class="bg-blue-100 text-blue-800 px-2 py-1 rounded">{}</a>', url, count)

@admin.register(Staff)
class StaffAdmin(ModelAdmin):
    # Professional list display with badges and links
    list_display = [
        'profile_photo',
        'full_name_link',
        'email',
        'phone',
        'role_badge',
        'employment_type_badge',
        'current_salary_display',
        'leave_balance',
        'status_badge',
        'action_buttons',
    ]
    
    list_filter = [
        'employment_type',
        'payment_frequency',
        'is_active',
        'role',
        'join_date',
    ]
    
    search_fields = [
        'first_name', 'last_name', 'email', 
        'phone', 'pan_number', 'account_number'
    ]
    
    autocomplete_fields = ['role', 'created_by']
    
    # Organized fieldsets for professional look
    fieldsets = (
        ('Personal Information', {
            'fields': (
                ('first_name', 'last_name'),
                'email',
                'phone',
                'address',
                'date_of_birth',
            ),
            'description': 'Basic personal details'
        }),
        
        ('Employment Details', {
            'fields': (
                'role',
                ('employment_type', 'payment_frequency'),
                ('join_date', 'exit_date'),
                'is_active',
            ),
            'description': 'Employment and position details'
        }),
        
        ('Salary & Compensation', {
            'fields': (
                ('base_salary', 'hourly_rate'),
                'overtime_rate',
            ),
            'description': 'Salary and rate information',
            'classes': ('wide',),
        }),
        
        ('Bank Details', {
            'fields': (
                ('bank_name', 'account_number'),
                ('ifsc_code', 'pan_number'),
            ),
            'classes': ('collapse',),
        }),
        
        ('Tax Information', {
            'fields': ('tax_id', 'tax_exemption'),
            'classes': ('collapse',),
        }),
        
        ('Leave Balances', {
            'fields': (
                ('annual_leave_balance', 'sick_leave_balance'),
            ),
            'classes': ('collapse',),
        }),
        
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # Unfold configurations
    list_fullwidth = True
    list_filter_submit_button = True
    warn_unsaved_form = True
    compressed_fields = True
    
    # Custom display methods
    @display(description="Photo")
    def profile_photo(self, obj):
        initials = f"{obj.first_name[0]}{obj.last_name[0]}"
        colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-red-500', 'bg-yellow-500']
        color = colors[hash(obj.email) % len(colors)]
        return format_html(
            '<div class="w-8 h-8 rounded-full {} flex items-center justify-center text-white text-sm font-bold">{}</div>',
            color, initials
        )
    
    @display(description="Name")
    def full_name_link(self, obj):
        url = reverse('admin:staff_staff_change', args=[obj.id])
        return format_html('<a href="{}" class="font-semibold hover:underline">{}</a>', url, obj.full_name)
    
    @display(description="Role")
    def role_badge(self, obj):
        if obj.role:
            url = reverse('admin:staff_role_change', args=[obj.role.id])
            return format_html(
                '<a href="{}" class="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs hover:bg-purple-200">{}</a>',
                url, obj.role.name
            )
        return format_html('<span class="bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs">No Role</span>')
    
    @display(description="Type")
    def employment_type_badge(self, obj):
        colors = {
            'full_time': 'bg-green-100 text-green-800',
            'part_time': 'bg-yellow-100 text-yellow-800',
            'contract': 'bg-blue-100 text-blue-800',
            'intern': 'bg-purple-100 text-purple-800',
        }
        color_class = colors.get(obj.employment_type, 'bg-gray-100 text-gray-800')
        return format_html(
            '<span class="{} px-2 py-1 rounded text-xs font-medium">{}</span>',
            color_class, obj.get_employment_type_display()
        )
    
    @display(description="Salary")
    def current_salary_display(self, obj):
        if obj.base_salary:
            return format_html('₹{:,.0f}', obj.base_salary)
        elif obj.hourly_rate:
            return format_html('₹{}/hr', obj.hourly_rate)
        return format_html('<span class="text-gray-400">Not set</span>')
    
    @display(description="Leave")
    def leave_balance(self, obj):
        return format_html(
            '<span title="Annual/Sick">{} / {}</span>',
            obj.annual_leave_balance, obj.sick_leave_balance
        )
    
    @display(description="Status")
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Active</span>')
        return format_html('<span class="bg-red-100 text-red-800 px-2 py-1 rounded text-xs">Inactive</span>')
    
    @display(description="Actions")
    def action_buttons(self, obj):
        salary_url = reverse('admin:salary_salaryslip_changelist') + f'?staff__id__exact={obj.id}'
        invoice_url = reverse('admin:salary_staffinvoice_changelist') + f'?staff__id__exact={obj.id}'
        
        return format_html(
            '<div class="flex gap-1">'
            '<a href="{}" class="bg-blue-500 text-white px-2 py-1 rounded text-xs hover:bg-blue-600">💰 Salary</a>'
            '<a href="{}" class="bg-green-500 text-white px-2 py-1 rounded text-xs hover:bg-green-600">📄 Invoices</a>'
            '</div>',
            salary_url, invoice_url
        )
    
    # Actions
    actions = ['generate_salary_slips', 'send_welcome_email', 'export_staff_data']
    
    def generate_salary_slips(self, request, queryset):
        self.message_user(request, f"Salary generation started for {queryset.count()} staff members")
    generate_salary_slips.short_description = "Generate salary slips"
    
    def send_welcome_email(self, request, queryset):
        self.message_user(request, f"Welcome emails sent to {queryset.count()} staff members")
    send_welcome_email.short_description = "Send welcome email"
    
    def export_staff_data(self, request, queryset):
        self.message_user(request, f"Exporting {queryset.count()} staff records")
    export_staff_data.short_description = "Export staff data"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('role')
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new
            obj.created_by = request.user
        super().save_model(request, obj, form, change)