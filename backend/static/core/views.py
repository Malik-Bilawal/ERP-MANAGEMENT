from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from clients.models import Client
from projects.models import Project
from payments.models import Payment
from datetime import datetime, timedelta

@staff_member_required
def admin_reports(request):
    context = {
        'title': 'Reports',
        'total_clients': Client.objects.count(),
        'total_projects': Project.objects.count(),
        'total_revenue': Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
        'pending_payments': Payment.objects.filter(status='pending').count(),
        'recent_projects': Project.objects.order_by('-created_at')[:10],
        'recent_payments': Payment.objects.order_by('-payment_date')[:10],
    }
    return render(request, 'admin/reports.html', context)

@staff_member_required
def admin_settings(request):
    return render(request, 'admin/settings.html', {'title': 'Settings'})

@staff_member_required
def admin_search(request):
    query = request.GET.get('q', '')
    results = {
        'clients': Client.objects.filter(name__icontains=query) | Client.objects.filter(company__icontains=query),
        'projects': Project.objects.filter(project_name__icontains=query),
        'payments': Payment.objects.filter(transaction_reference__icontains=query),
    }
    return render(request, 'admin/search_results.html', {'results': results, 'query': query})