from rest_framework import serializers
from .models import Project
from clients.serializers import ClientSerializer

class ProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    company_name = serializers.CharField(source='client.company', read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'project_id', 'client', 'client_name', 'company_name', 'project_name',
            'description', 'cost', 'actual_cost', 'deadline', 'status',
            'priority', 'start_date', 'completion_date', 'budget_variance',
            'budget_variance_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['project_id', 'budget_variance', 'budget_variance_percentage', 'created_at', 'updated_at']

class ProjectListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'project_id', 'project_name', 'client_name', 'cost',
            'actual_cost', 'status', 'priority', 'deadline'
        ]

class ProjectDetailSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    payments = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = '__all__'
    
    def get_payments(self, obj):
        from payments.serializers import PaymentSerializer
        payments = obj.payments.all()
        return PaymentSerializer(payments, many=True).data