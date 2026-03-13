from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Assignment
from .serializers import (
    AssignmentSerializer, 
    AssignmentDetailSerializer, 
    AssignmentCreateSerializer,
    AssignmentUpdateSerializer
)

class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all().select_related('staff', 'project')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'is_active', 'project', 'staff']
    search_fields = ['staff__first_name', 'staff__last_name', 'project__name', 'role_in_project']
    ordering_fields = ['assigned_date', 'end_date', 'priority', 'status']
    ordering = ['-assigned_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AssignmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AssignmentUpdateSerializer
        elif self.action == 'retrieve':
            return AssignmentDetailSerializer
        return AssignmentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by project
        project_id = self.request.query_params.get('project', None)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Filter by staff
        staff_id = self.request.query_params.get('staff', None)
        if staff_id:
            queryset = queryset.filter(staff_id=staff_id)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)
        if from_date:
            queryset = queryset.filter(assigned_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(assigned_date__lte=to_date)
        
        # Filter by overdue
        overdue = self.request.query_params.get('overdue', None)
        if overdue and overdue.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                end_date__lt=today,
                status__in=['pending', 'in_progress']
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update hours worked and progress"""
        assignment = self.get_object()
        hours = request.data.get('hours_worked', None)
        
        if hours is not None:
            try:
                assignment.hours_worked = float(hours)
                assignment.save()
                return Response({
                    'status': 'progress updated',
                    'progress': assignment.progress_percentage,
                    'hours_worked': assignment.hours_worked
                })
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid hours value'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {'error': 'hours_worked field required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def project_summary(self, request):
        """Get assignment summary by project"""
        project_id = request.query_params.get('project_id', None)
        
        if not project_id:
            return Response(
                {'error': 'project_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assignments = self.get_queryset().filter(project_id=project_id)
        
        summary = {
            'total_assignments': assignments.count(),
            'active_assignments': assignments.filter(is_active=True).count(),
            'by_status': assignments.values('status').annotate(count=Count('id')),
            'by_priority': assignments.values('priority').annotate(count=Count('id')),
            'total_hours_allocated': assignments.aggregate(total=Sum('hours_allocated'))['total'] or 0,
            'total_hours_worked': assignments.aggregate(total=Sum('hours_worked'))['total'] or 0,
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def staff_workload(self, request):
        """Get workload summary by staff"""
        from django.db.models import Count, Sum
        
        workload = Assignment.objects.filter(
            is_active=True,
            status__in=['pending', 'in_progress']
        ).values(
            'staff__id', 'staff__first_name', 'staff__last_name'
        ).annotate(
            project_count=Count('project', distinct=True),
            total_hours=Sum('hours_allocated'),
            high_priority=Count('id', filter=Q(priority='high') | Q(priority='critical'))
        )
        
        return Response(workload)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics"""
        today = timezone.now().date()
        
        stats = {
            'total_active': Assignment.objects.filter(is_active=True).count(),
            'overdue': Assignment.objects.filter(
                end_date__lt=today,
                status__in=['pending', 'in_progress']
            ).count(),
            'completed_this_month': Assignment.objects.filter(
                status='completed',
                end_date__month=today.month,
                end_date__year=today.year
            ).count(),
            'by_priority': Assignment.objects.filter(is_active=True).values('priority').annotate(
                count=Count('id')
            ),
            'recent_assignments': AssignmentSerializer(
                Assignment.objects.filter(is_active=True).order_by('-assigned_date')[:5],
                many=True
            ).data
        }
        
        return Response(stats)