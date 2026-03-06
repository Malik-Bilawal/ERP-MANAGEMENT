from rest_framework import serializers
from .models import Client

class ClientSerializer(serializers.ModelSerializer):
    total_projects = serializers.IntegerField(source='projects.count', read_only=True)
    total_payments = serializers.DecimalField(
        max_digits=15, 
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Client
        fields = [
            'client_id', 'name', 'company', 'email', 'phone', 'address',
            'total_revenue_generated', 'total_projects', 'total_payments',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['client_id', 'total_revenue_generated', 'created_at', 'updated_at']

class ClientDetailSerializer(serializers.ModelSerializer):
    projects = serializers.SerializerMethodField()
    recent_payments = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = '__all__'
    
    def get_projects(self, obj):
        from projects.serializers import ProjectListSerializer
        projects = obj.projects.all()[:5]  # Last 5 projects
        return ProjectListSerializer(projects, many=True).data
    
    def get_recent_payments(self, obj):
        from payments.serializers import PaymentSerializer
        payments = obj.payments.all()[:5]  # Last 5 payments
        return PaymentSerializer(payments, many=True).data