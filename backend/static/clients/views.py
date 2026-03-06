from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q
from django_filters.rest_framework import DjangoFilterBackend
from .models import Client
from .serializers import ClientSerializer, ClientDetailSerializer
from payments.models import Payment

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'company']
    search_fields = ['name', 'company', 'email']
    ordering_fields = ['name', 'company', 'total_revenue_generated', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClientDetailSerializer
        return ClientSerializer
    
    @action(detail=True, methods=['get'])
    def projects(self, request, pk=None):
        client = self.get_object()
        projects = client.projects.all()
        from projects.serializers import ProjectListSerializer
        serializer = ProjectListSerializer(projects, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        client = self.get_object()
        payments = client.payments.all()
        from payments.serializers import PaymentSerializer
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def payment_summary(self, request, pk=None):
        client = self.get_object()
        payments = client.payments.all()
        
        summary = {
            'total_paid': payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_pending': payments.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_overdue': payments.filter(
                status='pending', 
                due_date__lt=request.query_params.get('date')
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        total_clients = Client.objects.count()
        active_clients = Client.objects.filter(is_active=True).count()
        total_revenue = Client.objects.aggregate(Sum('total_revenue_generated'))['total_revenue_generated__sum'] or 0
        
        stats = {
            'total_clients': total_clients,
            'active_clients': active_clients,
            'total_revenue': total_revenue,
        }
        
        return Response(stats)