from rest_framework import serializers
from .models import Assignment
from staff.models import Staff
from projects.models import Project
from staff.serializers import StaffSerializer
from projects.serializers import ProjectSerializer

class AssignmentSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    project_details = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    priority_display = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = ['assigned_date', 'created_at', 'updated_at', 'hours_worked']
    
    def get_staff_name(self, obj):
        return f"{obj.staff.first_name} {obj.staff.last_name}" if obj.staff else ""
    
    def get_project_name(self, obj):
        return obj.project.name if obj.project else ""
    
    def get_project_details(self, obj):
        """Get key project information"""
        if obj.project:
            return {
                'id': obj.project.id,
                'name': obj.project.name,
                'status': getattr(obj.project, 'status', 'N/A'),
                'client': getattr(obj.project.client, 'name', 'N/A') if hasattr(obj.project, 'client') else 'N/A'
            }
        return None
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_priority_display(self, obj):
        return obj.get_priority_display()
    
    def get_progress(self, obj):
        return obj.progress_percentage

class AssignmentDetailSerializer(serializers.ModelSerializer):
    staff_details = StaffSerializer(source='staff', read_only=True)
    project_full_details = ProjectSerializer(source='project', read_only=True)
    status_display = serializers.SerializerMethodField()
    priority_display = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = ['assigned_date', 'created_at', 'updated_at']
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_priority_display(self, obj):
        return obj.get_priority_display()
    
    def get_progress(self, obj):
        return obj.progress_percentage
    
    def get_is_overdue(self, obj):
        return obj.is_overdue

class AssignmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = ['assigned_date', 'created_at', 'updated_at', 'hours_worked']
    
    def validate(self, data):
        # Check if staff is already assigned to this project
        if data.get('is_active', True):
            existing = Assignment.objects.filter(
                staff=data['staff'],
                project=data['project'],
                is_active=True,
                status__in=['pending', 'in_progress']
            ).exclude(status='completed').exists()
            
            if existing:
                raise serializers.ValidationError(
                    "This staff member is already actively assigned to this project."
                )
        
        # Validate dates
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    "End date must be after start date."
                )
        
        return data

class AssignmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['status', 'priority', 'hours_worked', 'end_date', 'notes']