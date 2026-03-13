from rest_framework import serializers
from .models import Staff, Role

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class StaffSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Staff
        fields = '__all__'
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"