# services/serializers.py
from rest_framework import serializers
from .models import (
    ServiceCategory, Service, SubService, ClientService,
    ServicePricingHistory, ServiceCategoryAnalytics
)

class ServiceCategorySerializer(serializers.ModelSerializer):
    total_sub_services = serializers.IntegerField(read_only=True)
    total_clients = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'icon', 'color_code', 'is_active', 
                 'total_sub_services', 'total_clients', 'created_at']
        read_only_fields = ['id', 'created_at']

class ServiceSerializer(serializers.ModelSerializer):
    service_category_name = serializers.CharField(source='service_category.name', read_only=True)
    total_sub_services = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Service
        fields = ['id', 'service_category', 'service_category_name', 'name', 
                 'description', 'base_price', 'is_active', 'total_sub_services', 
                 'created_at']
        read_only_fields = ['id', 'created_at']

class SubServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_category = serializers.CharField(source='service.service_category.name', read_only=True)
    formatted_price = serializers.CharField(read_only=True)
    
    class Meta:
        model = SubService
        fields = ['id', 'service', 'service_name', 'service_category', 'name', 
                 'description', 'code', 'price', 'formatted_price', 
                 'estimated_duration_days', 'is_active', 'requires_approval', 
                 'created_at']
        read_only_fields = ['id', 'code', 'created_at']

class ClientServiceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    sub_service_name = serializers.CharField(source='sub_service.name', read_only=True)
    sub_service_code = serializers.CharField(source='sub_service.code', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ClientService
        fields = ['id', 'client', 'client_name', 'sub_service', 'sub_service_name', 
                 'sub_service_code', 'assigned_to', 'assigned_to_name', 'start_date', 
                 'end_date', 'custom_price', 'final_price', 'status', 'notes', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ServicePricingHistorySerializer(serializers.ModelSerializer):
    sub_service_name = serializers.CharField(source='sub_service.name', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = ServicePricingHistory
        fields = ['id', 'sub_service', 'sub_service_name', 'old_price', 'new_price', 
                 'changed_by', 'changed_by_name', 'changed_at', 'reason']
        read_only_fields = ['id', 'changed_at']

# Add this missing serializer
class ServiceCategoryAnalyticsSerializer(serializers.ModelSerializer):
    service_category_name = serializers.CharField(source='service_category.name', read_only=True)
    
    class Meta:
        model = ServiceCategoryAnalytics
        fields = ['id', 'service_category', 'service_category_name', 'month', 
                 'total_revenue', 'total_clients', 'total_projects', 'created_at']
        read_only_fields = ['id', 'created_at']