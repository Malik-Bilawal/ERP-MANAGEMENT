from rest_framework import serializers
from .models import (
    Client, Project, ProjectService, TimeEntry,
    Milestone, ClientDocument, ClientCommunication
)
from services.serializers import SubServiceSerializer


class ClientSerializer(serializers.ModelSerializer):
    total_projects = serializers.IntegerField(read_only=True)
    active_projects = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    pending_payments = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ['client_id', 'created_at', 'updated_at', 'created_by']



class ProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_manager_name = serializers.CharField(source='project_manager.get_full_name', read_only=True)
    total_hours_worked = serializers.IntegerField(read_only=True)
    total_billable_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['project_id', 'total_cost', 'created_at', 'updated_at', 'created_by']


class ProjectServiceSerializer(serializers.ModelSerializer):
    sub_service_details = SubServiceSerializer(source='sub_service', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = ProjectService
        fields = '__all__'
        read_only_fields = ['created_at']


class TimeEntrySerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    billable_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = TimeEntry
        fields = '__all__'
        read_only_fields = ['created_at', 'approved_at']


class MilestoneSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = Milestone
        fields = '__all__'
        read_only_fields = ['created_at']


class ClientDocumentSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = ClientDocument
        fields = '__all__'
        read_only_fields = ['uploaded_at']


class ClientCommunicationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    conducted_by_name = serializers.CharField(source='conducted_by.get_full_name', read_only=True)
    
    class Meta:
        model = ClientCommunication
        fields = '__all__'
        read_only_fields = ['created_at']