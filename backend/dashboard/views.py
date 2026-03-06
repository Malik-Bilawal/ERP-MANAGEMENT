from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
import json
import os
from django.conf import settings  # <-- ADD THIS LINE


from clients.models import Client
from projects.models import Project
from payments.models import Payment

@staff_member_required
def admin_dashboard(request):
    # Get date ranges
    today = timezone.now()
    
    # Basic stats
    total_clients = Client.objects.count()
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(status='active').count()
    total_revenue = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Monthly revenue data for chart
    monthly_revenue = []
    months = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_start = datetime(month_date.year, month_date.month, 1).date()
        
        if i == 0:
            month_end = today.date()
        else:
            if month_date.month == 12:
                month_end = datetime(month_date.year + 1, 1, 1).date() - timedelta(days=1)
            else:
                month_end = datetime(month_date.year, month_date.month + 1, 1).date() - timedelta(days=1)
        
        revenue = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lte=month_end,
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        monthly_revenue.append(float(revenue))
        months.append(month_start.strftime('%b %Y'))
    
    # Project status distribution
    project_status = {
        'pending': Project.objects.filter(status='pending').count(),
        'active': Project.objects.filter(status='active').count(),
        'completed': Project.objects.filter(status='completed').count(),
        'cancelled': Project.objects.filter(status='cancelled').count(),
    }
    
    # Recent payments
    recent_payments = Payment.objects.select_related('project__client').order_by('-payment_date')[:10]
    
    # Top clients by revenue
    top_clients = Client.objects.annotate(
        total_revenue=Sum('projects__payments__amount')
    ).order_by('-total_revenue')[:5]
    
    context = {
        'total_clients': total_clients,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_revenue': total_revenue,
        'monthly_revenue': json.dumps(monthly_revenue),
        'months': json.dumps(months),
        'project_status': project_status,
        'recent_payments': recent_payments,
        'top_clients': top_clients,
        'site_title': 'SRF IMS',  # Add site title for the template
        'site_header': 'SRF Integrated Management System',
    }
    
    # Try to render with Unfold template
    try:
        return render(request, 'admin/dashboard.html', context)
    except TemplateDoesNotExist:
        # Fallback to direct rendering if template doesn't exist
        template_path = os.path.join(settings.BASE_DIR, 'dashboard', 'templates', 'admin', 'dashboard.html')
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as file:
                template_string = file.read()
            from django.template import Template, Context
            template = Template(template_string)
            html = template.render(Context(context))
            return HttpResponse(html)
        else:
            return HttpResponse(f"Template not found at: {template_path}")