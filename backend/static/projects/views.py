from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q, Avg, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Project
from .serializers import ProjectSerializer, ProjectListSerializer, ProjectDetailSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'client']
    search_fields = ['project_name', 'description', 'client__name', 'client__company']
    ordering_fields = ['project_name', 'cost', 'deadline', 'status', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectSerializer
    
    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        project = self.get_object()
        payments = project.payments.all()
        from payments.serializers import PaymentSerializer
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_actual_cost(self, request, pk=None):
        project = self.get_object()
        actual_cost = request.data.get('actual_cost')
        
        if actual_cost is not None:
            project.actual_cost = actual_cost
            project.save()
            return Response({'message': 'Actual cost updated successfully', 'budget_variance': project.budget_variance})
        
        return Response({'error': 'Actual cost is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(status='in_progress').count()
        completed_projects = Project.objects.filter(status='completed').count()
        total_budget = Project.objects.aggregate(Sum('cost'))['cost__sum'] or 0
        total_actual = Project.objects.aggregate(Sum('actual_cost'))['actual_cost__sum'] or 0
        
        status_counts = Project.objects.values('status').annotate(count=Count('status'))
        priority_counts = Project.objects.values('priority').annotate(count=Count('priority'))
        
        # Projects nearing deadline (next 7 days)
        upcoming_deadlines = Project.objects.filter(
            status__in=['planned', 'in_progress'],
            deadline__gte=timezone.now().date(),
            deadline__lte=timezone.now().date() + timezone.timedelta(days=7)
        ).count()
        
        # Overdue projects
        overdue_projects = Project.objects.filter(
            status__in=['planned', 'in_progress'],
            deadline__lt=timezone.now().date()
        ).count()
        
        stats = {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'total_budget': total_budget,
            'total_actual': total_actual,
            'budget_variance': total_budget - total_actual,
            'upcoming_deadlines': upcoming_deadlines,
            'overdue_projects': overdue_projects,
            'status_breakdown': list(status_counts),
            'priority_breakdown': list(priority_counts),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def budget_variance_report(self, request):
        projects = Project.objects.all()
        
        report = []
        for project in projects:
            report.append({
                'project_id': project.project_id,
                'project_name': project.project_name,
                'client_name': project.client.name,
                'budgeted_cost': float(project.cost),
                'actual_cost': float(project.actual_cost),
                'variance': float(project.budget_variance),
                'variance_percentage': float(project.budget_variance_percentage),
                'status': project.status,
            })
        
        return Response(report)