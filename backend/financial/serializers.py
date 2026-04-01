from rest_framework import serializers
from .models import Invoice, Revenue, ClientBalance, CompanyRevenue, Payment

class InvoiceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_budget = serializers.DecimalField(source='project.budget', max_digits=15, decimal_places=2, read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_id', 'invoice_number', 'client', 'client_name',
            'project', 'project_name', 'project_budget', 'amount', 'amount_paid',
            'remaining_amount', 'status', 'invoice_date', 'notes', 'created_at', 'created_by'
        ]
        read_only_fields = ['invoice_id', 'invoice_number', 'amount_paid', 'status', 'created_at', 'created_by']


class PaymentSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    remaining_amount = serializers.SerializerMethodField()
    invoice_total = serializers.SerializerMethodField()
    invoice_paid = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'invoice', 'invoice_number', 'client', 'client_name',
            'project', 'project_name', 'amount', 'payment_method', 'payment_date',
            'transaction_reference', 'notes', 'created_at', 'created_by',
            'remaining_amount', 'invoice_total', 'invoice_paid'
        ]
        read_only_fields = ['payment_id', 'client', 'project', 'created_at', 'created_by']
    
    def get_remaining_amount(self, obj):
        if obj.invoice:
            return float(obj.invoice.remaining_amount)
        return 0
    
    def get_invoice_total(self, obj):
        if obj.invoice:
            return float(obj.invoice.amount)
        return 0
    
    def get_invoice_paid(self, obj):
        if obj.invoice:
            return float(obj.invoice.amount_paid)
        return 0


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