from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    Client, Project, ProjectService, TimeEntry,
    Milestone, ClientDocument, ClientCommunication
)
from .serializers import (
    ClientSerializer, ProjectSerializer, ProjectServiceSerializer,
    TimeEntrySerializer, MilestoneSerializer, ClientDocumentSerializer,
    ClientCommunicationSerializer
)

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone', 'company_name', 'client_id']
    ordering_fields = ['created_at', 'name', 'status', 'total_revenue']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by client type
        client_type = self.request.query_params.get('client_type')
        if client_type:
            queryset = queryset.filter(client_type=client_type)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def projects(self, request, pk=None):
        """Get all projects for a client"""
        client = self.get_object()
        projects = client.projects.all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def communications(self, request, pk=None):
        """Get all communications for a client"""
        client = self.get_object()
        communications = client.communications.all()[:50]
        serializer = ClientCommunicationSerializer(communications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def financial_summary(self, request, pk=None):
        """Get financial summary for a client"""
        client = self.get_object()
        return Response({
            'total_revenue': client.total_revenue,
            'pending_payments': client.pending_payments,
            'total_projects': client.total_projects,
            'active_projects': client.active_projects,
            'credit_limit': client.credit_limit,
            'credit_available': client.credit_limit - client.pending_payments,
        })


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'project_id', 'client__name', 'description']
    ordering_fields = ['created_at', 'start_date', 'estimated_end_date', 'status', 'priority']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by client
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter by project manager
        manager_id = self.request.query_params.get('manager')
        if manager_id:
            queryset = queryset.filter(project_manager_id=manager_id)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def time_entries(self, request, pk=None):
        """Get all time entries for a project"""
        project = self.get_object()
        time_entries = project.time_entries.all()
        serializer = TimeEntrySerializer(time_entries, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def milestones(self, request, pk=None):
        """Get all milestones for a project"""
        project = self.get_object()
        milestones = project.milestones.all()
        serializer = MilestoneSerializer(milestones, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_service(self, request, pk=None):
        """Add a service to project"""
        project = self.get_object()
        sub_service_id = request.data.get('sub_service_id')
        custom_price = request.data.get('custom_price')
        quantity = request.data.get('quantity', 1)
        
        project_service, created = ProjectService.objects.get_or_create(
            project=project,
            sub_service_id=sub_service_id,
            defaults={
                'custom_price': custom_price,
                'quantity': quantity,
                'notes': request.data.get('notes', '')
            }
        )
        
        if not created:
            return Response({'error': 'Service already assigned to this project'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ProjectServiceSerializer(project_service)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def add_time_entry(self, request, pk=None):
        """Add time entry to project"""
        project = self.get_object()
        data = request.data.copy()
        data['project'] = project.id
        data['user'] = request.user.id
        
        serializer = TimeEntrySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update project progress"""
        project = self.get_object()
        progress = request.data.get('progress_percentage')
        notes = request.data.get('completion_notes')
        
        if progress is not None:
            project.progress_percentage = progress
        if notes:
            project.completion_notes = notes
        
        if progress == 100:
            project.status = 'completed'
            project.actual_end_date = timezone.now().date()
        
        project.save()
        serializer = self.get_serializer(project)
        return Response(serializer.data)


class TimeEntryViewSet(viewsets.ModelViewSet):
    queryset = TimeEntry.objects.all()
    serializer_class = TimeEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['project__name', 'description']
    ordering_fields = ['date', 'hours', 'created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by project
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve time entry"""
        time_entry = self.get_object()
        time_entry.is_approved = True
        time_entry.approved_by = request.user
        time_entry.approved_at = timezone.now()
        time_entry.save()
        
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject time entry"""
        time_entry = self.get_object()
        time_entry.is_approved = False
        time_entry.approved_by = request.user
        time_entry.approved_at = timezone.now()
        time_entry.save()
        
        return Response({'status': 'rejected'})


class MilestoneViewSet(viewsets.ModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'project__name']


class ClientDocumentViewSet(viewsets.ModelViewSet):
    queryset = ClientDocument.objects.all()
    serializer_class = ClientDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'client__name']
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class ClientCommunicationViewSet(viewsets.ModelViewSet):
    queryset = ClientCommunication.objects.all()
    serializer_class = ClientCommunicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['subject', 'content', 'client__name']
    ordering_fields = ['date', 'created_at']
    
    def perform_create(self, serializer):
        serializer.save(conducted_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_followup_completed(self, request, pk=None):
        """Mark follow-up as completed"""
        communication = self.get_object()
        communication.follow_up_completed = True
        communication.save()
        return Response({'status': 'follow-up marked as completed'})