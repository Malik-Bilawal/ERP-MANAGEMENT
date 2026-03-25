from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Invoice, Revenue, ClientBalance, CompanyRevenue
from .serializers import (
    InvoiceSerializer, RevenueSerializer, ClientBalanceSerializer, CompanyRevenueSerializer
)
from client_management.models import Client, Project

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_id', 'client__name', 'project__name']
    ordering_fields = ['invoice_date', 'amount']
    
    def perform_create(self, serializer):
        """Auto-set created_by"""
        serializer.save(created_by=self.request.user)


class RevenueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Revenue.objects.all()
    serializer_class = RevenueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['client__name', 'project__name']
    ordering_fields = ['revenue_date', 'amount']


class ClientBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClientBalance.objects.all()
    serializer_class = ClientBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['client__name']


class CompanyRevenueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CompanyRevenue.objects.all()
    serializer_class = CompanyRevenueSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get real-time dashboard data"""
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        
        # Total Company Revenue (All time)
        total_revenue = Revenue.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Current Month Revenue
        current_month_revenue = Revenue.objects.filter(
            revenue_date__gte=start_of_month,
            revenue_date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Total Pending Payments (All clients)
        total_pending = ClientBalance.objects.aggregate(
            total=Sum('pending_balance')
        )['total'] or 0
        
        # Total Clients
        total_clients = Client.objects.filter(status='active').count()
        
        # Total Projects
        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(status='in_progress').count()
        
        # Top Paying Clients
        top_clients = ClientBalance.objects.filter(
            total_invoiced__gt=0
        ).order_by('-total_invoiced')[:5]
        
        top_clients_data = []
        for client in top_clients:
            top_clients_data.append({
                'name': client.client.name,
                'total_paid': client.total_invoiced,
                'pending': client.pending_balance,
                'percentage': (client.total_invoiced / client.total_projects_cost * 100) if client.total_projects_cost > 0 else 0
            })
        
        # Recent Invoices (Last 5)
        recent_invoices = Invoice.objects.all()[:5]
        recent_invoices_data = InvoiceSerializer(recent_invoices, many=True).data
        
        # Monthly Revenue Trend (Last 6 months)
        monthly_trend = []
        for i in range(5, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            if i == 0:
                month_end = today
            else:
                next_month = month_date.replace(day=28) + timedelta(days=4)
                month_end = next_month - timedelta(days=next_month.day)
            
            monthly_revenue = Revenue.objects.filter(
                revenue_date__gte=month_start,
                revenue_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_trend.append({
                'month': month_start.strftime('%B %Y'),
                'revenue': monthly_revenue
            })
        
        return Response({
            'summary': {
                'total_company_revenue': total_revenue,
                'current_month_revenue': current_month_revenue,
                'total_pending_payments': total_pending,
                'total_clients': total_clients,
                'total_projects': total_projects,
                'active_projects': active_projects,
            },
            'top_clients': top_clients_data,
            'recent_invoices': recent_invoices_data,
            'monthly_trend': monthly_trend,
            'last_updated': timezone.now()
        })


class DashboardViewSet(viewsets.ViewSet):
    """Simple Dashboard"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get quick stats"""
        total_revenue = Revenue.objects.aggregate(total=Sum('amount'))['total'] or 0
        total_pending = ClientBalance.objects.aggregate(total=Sum('pending_balance'))['total'] or 0
        total_clients = Client.objects.filter(status='active').count()
        total_projects = Project.objects.count()
        
        return Response({
            'total_revenue': total_revenue,
            'pending_payments': total_pending,
            'total_clients': total_clients,
            'total_projects': total_projects
        })