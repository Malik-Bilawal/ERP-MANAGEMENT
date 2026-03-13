from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path('', lambda request: redirect('admin/')),  # Redirect root to admin
    path('admin/reports/', core_views.admin_reports, name='admin_reports'),
    path('admin/dashboard/', include('dashboard.urls')),
    path('admin/settings/', core_views.admin_settings, name='admin_settings'),
    path('admin/search/', core_views.admin_search, name='admin_search'),
    path('admin/', admin.site.urls),
    path('api/', include('clients.urls')),
    path('api/', include('projects.urls')),
    path('api/', include('payments.urls')),


    path('api/staff/', include('staff.urls')),
    path('api/assignments/', include('assignments.urls')),
    path('api/salary/', include('salary.urls')),
    
    path('api-auth/', include('rest_framework.urls')),

]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)