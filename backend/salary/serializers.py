# salary/serializers.py
from rest_framework import serializers
from .models import SalaryStructure, SalaryAssignment, SalarySlip, StaffInvoice, InvoiceLineItem
from staff.models import Staff
from projects.models import Project

class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = '__all__'

class SalaryAssignmentSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    structure_name = serializers.CharField(source='salary_structure.name', read_only=True)
    
    class Meta:
        model = SalaryAssignment
        fields = '__all__'
    
    def get_staff_name(self, obj):
        return str(obj.staff)

class SalarySlipSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    month_display = serializers.SerializerMethodField()
    
    class Meta:
        model = SalarySlip
        fields = '__all__'
    
    def get_staff_name(self, obj):
        return str(obj.staff)
    
    def get_month_display(self, obj):
        return obj.month.strftime('%B %Y')

class StaffInvoiceSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    balance_due = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffInvoice
        fields = '__all__'
    
    def get_staff_name(self, obj):
        return str(obj.staff)
    
    def get_project_name(self, obj):
        return obj.project.project_name if obj.project else None
    
    def get_balance_due(self, obj):
        return obj.balance_due
    
    def get_is_overdue(self, obj):
        return obj.is_overdue

class InvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLineItem
        fields = '__all__'

# If you need a Staff serializer for reference
class StaffBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['id', 'first_name', 'last_name', 'email']

# If you need a Project serializer for reference
class ProjectBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'project_name', 'client']