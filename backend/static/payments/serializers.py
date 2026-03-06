from rest_framework import serializers
from .models import Payment, Invoice
from clients.serializers import ClientSerializer
from projects.serializers import ProjectListSerializer

class PaymentSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'payment_id', 'client', 'client_name', 'project', 'project_name',
            'amount', 'payment_date', 'due_date', 'status', 'payment_method',
            'transaction_reference', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['payment_id', 'payment_date', 'created_at', 'updated_at']

class PaymentDetailSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True)
    invoice = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = '__all__'
    
    def get_invoice(self, obj):
        if hasattr(obj, 'invoice'):
            return InvoiceSerializer(obj.invoice).data
        return None

class InvoiceSerializer(serializers.ModelSerializer):
    payment_details = PaymentSerializer(source='payment', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'invoice_id', 'invoice_number', 'payment', 'payment_details',
            'generated_date', 'pdf_file', 'is_sent', 'sent_date'
        ]
        read_only_fields = ['invoice_id', 'invoice_number', 'generated_date']