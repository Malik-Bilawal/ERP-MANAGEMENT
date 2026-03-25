from rest_framework import serializers
from .models import Invoice, Revenue, ClientBalance, CompanyRevenue

class InvoiceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_budget = serializers.DecimalField(source='project.budget', max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_id', 'invoice_number', 'client', 'client_name',
            'project', 'project_name', 'project_budget', 'amount',
            'invoice_date', 'notes', 'created_at', 'created_by'
        ]
        read_only_fields = ['invoice_id', 'invoice_number', 'created_at', 'created_by']


class RevenueSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = Revenue
        fields = ['id', 'revenue_id', 'client', 'client_name', 'project', 
                  'project_name', 'amount', 'revenue_date', 'description', 'created_at']
        read_only_fields = ['revenue_id', 'created_at']


class ClientBalanceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    
    class Meta:
        model = ClientBalance
        fields = [
            'id', 'client', 'client_name', 'opening_balance',
            'total_invoiced', 'total_projects_cost', 'pending_balance',
            'last_updated'
        ]
        read_only_fields = ['last_updated']


class CompanyRevenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyRevenue
        fields = ['id', 'revenue_id', 'date', 'total_revenue', 
                  'total_clients', 'total_projects', 'active_projects', 'updated_at']
        read_only_fields = ['revenue_id', 'updated_at']