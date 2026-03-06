from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

class DashboardAdminSite(admin.AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        # Add dashboard link to the top
        app_list.insert(0, {
            'name': 'Dashboard',
            'app_label': 'dashboard',
            'models': [{
                'name': 'Main Dashboard',
                'object_name': 'dashboard',
                'admin_url': reverse('admin_dashboard'),
                'view_only': True,
            }]
        })
        return app_list

# If you want to replace the default admin site
# admin_site = DashboardAdminSite(name='myadmin')