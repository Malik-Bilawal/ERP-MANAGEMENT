from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta
from .models import Payment, Invoice
from .serializers import PaymentSerializer, PaymentDetailSerializer, InvoiceSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'client', 'project']
    search_fields = ['transaction_reference', 'client__name', 'project__project_name']
    ordering_fields = ['amount', 'payment_date', 'due_date', 'status']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaymentDetailSerializer
        return PaymentSerializer
    
    def perform_create(self, serializer):
        payment = serializer.save()
        # Update client's total revenue
        client = payment.client
        client.total_revenue_generated += payment.amount
        client.save()
    
    @action(detail=True, methods=['post'])
    def mark_as_completed(self, request, pk=None):
        payment = self.get_object()
        payment.status = 'completed'
        payment.transaction_reference = request.data.get('transaction_reference', '')
        payment.save()
        
        # Generate invoice automatically
        invoice = Invoice.objects.create(payment=payment)
        
        return Response({
            'message': 'Payment marked as completed',
            'payment': PaymentSerializer(payment).data,
            'invoice': InvoiceSerializer(invoice).data
        })
    
    @action(detail=True, methods=['post'])
    def generate_invoice(self, request, pk=None):
        payment = self.get_object()
        
        if hasattr(payment, 'invoice'):
            return Response({'error': 'Invoice already exists for this payment'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        invoice = Invoice.objects.create(payment=payment)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        total_payments = Payment.objects.count()
        total_amount = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        pending_amount = Payment.objects.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Overdue payments
        overdue_payments = Payment.objects.filter(
            status='pending',
            due_date__lt=timezone.now().date()
        )
        overdue_count = overdue_payments.count()
        overdue_amount = overdue_payments.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Monthly revenue (last 6 months)
        six_months_ago = timezone.now().date() - timedelta(days=180)
        monthly_revenue = Payment.objects.filter(
            status='completed',
            payment_date__gte=six_months_ago
        ).extra({'month': "MONTH(payment_date)", 'year': "YEAR(payment_date)"}).values('month', 'year').annotate(
            total=Sum('amount')
        ).order_by('year', 'month')
        
        stats = {
            'total_payments': total_payments,
            'total_amount': total_amount,
            'pending_amount': pending_amount,
            'overdue_count': overdue_count,
            'overdue_amount': overdue_amount,
            'monthly_revenue': list(monthly_revenue),
        }
        
        return Response(stats)

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_sent']
    search_fields = ['invoice_number', 'payment__client__name']
    ordering_fields = ['generated_date', 'invoice_number']
    
    @action(detail=True, methods=['post'])
    def mark_as_sent(self, request, pk=None):
        invoice = self.get_object()
        invoice.is_sent = True
        invoice.sent_date = timezone.now().date()
        invoice.save()
        
        return Response({'message': 'Invoice marked as sent'})