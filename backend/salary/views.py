# salary/views.py
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import SalaryStructure, SalaryAssignment, SalarySlip, StaffInvoice, InvoiceLineItem
from .serializers import (
    SalaryStructureSerializer, SalaryAssignmentSerializer, 
    SalarySlipSerializer, StaffInvoiceSerializer, InvoiceLineItemSerializer
)

class SalaryStructureViewSet(viewsets.ModelViewSet):
    queryset = SalaryStructure.objects.all()
    serializer_class = SalaryStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

class SalaryAssignmentViewSet(viewsets.ModelViewSet):
    queryset = SalaryAssignment.objects.select_related('staff', 'salary_structure').all()
    serializer_class = SalaryAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_current', 'staff', 'salary_structure']
    search_fields = ['staff__first_name', 'staff__last_name']
    ordering_fields = ['effective_from', 'created_at']

class SalarySlipViewSet(viewsets.ModelViewSet):
    queryset = SalarySlip.objects.select_related('staff', 'salary_structure', 'generated_by').all()
    serializer_class = SalarySlipSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'staff', 'month']
    search_fields = ['staff__first_name', 'staff__last_name']
    ordering_fields = ['month', 'created_at', 'net_pay']

class StaffInvoiceViewSet(viewsets.ModelViewSet):
    queryset = StaffInvoice.objects.select_related('staff', 'project', 'created_by').all()
    serializer_class = StaffInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'staff', 'project']
    search_fields = ['invoice_number', 'staff__first_name', 'staff__last_name']
    ordering_fields = ['invoice_date', 'due_date', 'total_amount']

class InvoiceLineItemViewSet(viewsets.ModelViewSet):
    queryset = InvoiceLineItem.objects.select_related('invoice').all()
    serializer_class = InvoiceLineItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['invoice']
    search_fields = ['description']