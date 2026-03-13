from rest_framework import viewsets
from .models import Staff, Role
from .serializers import StaffSerializer, RoleSerializer

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    filterset_fields = ['employment_type', 'is_active', 'role']
    search_fields = ['first_name', 'last_name', 'email']