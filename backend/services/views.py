from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    ServiceCategory, Service, SubService, ClientService,
    ServicePricingHistory, ServiceCategoryAnalytics
)
from .serializers import (
    ServiceCategorySerializer, ServiceSerializer, SubServiceSerializer,
    ClientServiceSerializer, ServicePricingHistorySerializer,
    ServiceCategoryAnalyticsSerializer
)

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'total_sub_services']
    
    @action(detail=True, methods=['get'])
    def services(self, request, pk=None):
        """Get all services under this category"""
        category = self.get_object()
        services = category.services.filter(is_active=True)
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for this category"""
        category = self.get_object()
        analytics = category.analytics.all()[:12]  # Last 12 months
        serializer = ServiceCategoryAnalyticsSerializer(analytics, many=True)
        return Response(serializer.data)

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'service_category__name']
    ordering_fields = ['name', 'base_price', 'created_at']
    
    @action(detail=True, methods=['get'])
    def sub_services(self, request, pk=None):
        """Get all sub-services under this service"""
        service = self.get_object()
        sub_services = service.sub_services.filter(is_active=True)
        serializer = SubServiceSerializer(sub_services, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def client_count(self, request, pk=None):
        """Get number of clients using this service"""
        service = self.get_object()
        count = ClientService.objects.filter(
            sub_service__service=service,
            status='active'
        ).values('client').distinct().count()
        return Response({'total_clients': count})

class SubServiceViewSet(viewsets.ModelViewSet):
    queryset = SubService.objects.all()
    serializer_class = SubServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description', 'service__name']
    ordering_fields = ['name', 'price', 'estimated_duration_days']
    
    @action(detail=True, methods=['post'])
    def assign_to_client(self, request, pk=None):
        """Assign this sub-service to a client"""
        sub_service = self.get_object()
        client_id = request.data.get('client_id')
        custom_price = request.data.get('custom_price')
        
        if not client_id:
            return Response({'error': 'client_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        client_service = ClientService.objects.create(
            client_id=client_id,
            sub_service=sub_service,
            custom_price=custom_price,
            status='pending',
            created_by=request.user
        )
        
        serializer = ClientServiceSerializer(client_service)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def pricing_history(self, request, pk=None):
        """Get pricing history for this sub-service"""
        sub_service = self.get_object()
        history = sub_service.pricing_history.all()[:20]
        serializer = ServicePricingHistorySerializer(history, many=True)
        return Response(serializer.data)

class ClientServiceViewSet(viewsets.ModelViewSet):
    queryset = ClientService.objects.all()
    serializer_class = ClientServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['client__name', 'sub_service__name', 'sub_service__code']
    ordering_fields = ['created_at', 'start_date', 'status', 'final_price']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by client if specified
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter by status if specified
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by service category if specified
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(sub_service__service__service_category_id=category_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def active_services(self, request):
        """Get all active client services"""
        active_services = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(active_services, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update status of a client service"""
        client_service = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(ClientService.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        client_service.status = new_status
        client_service.save()
        
        return Response({'status': 'updated', 'new_status': new_status})