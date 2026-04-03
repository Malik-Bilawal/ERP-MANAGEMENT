from rest_framework import serializers
from .models import Invoice, InvoiceItem, Payment, ClientLedger, ClientBalance, Revenue, CompanyRevenue


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['id', 'description', 'quantity', 'unit_price', 'total']
        read_only_fields = ['total']


class InvoiceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_budget = serializers.DecimalField(source='project.budget', max_digits=15, decimal_places=2, read_only=True)
    remaining_amount = serializers.SerializerMethodField()
    items = InvoiceItemSerializer(many=True, read_only=True)
    payment_count = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_id', 'invoice_number', 'client', 'client_name',
            'project', 'project_name', 'project_budget', 'amount', 'amount_paid',
            'remaining_amount', 'status', 'invoice_date', 'due_date', 'notes',
            'created_at', 'created_by', 'items', 'payment_count'
        ]
        read_only_fields = ['invoice_id', 'invoice_number', 'amount_paid', 'status', 'created_at', 'created_by']

    def get_remaining_amount(self, obj):
        return float(obj.remaining_amount)

    def get_payment_count(self, obj):
        return obj.payments.count()


class InvoiceCreateSerializer(serializers.ModelSerializer):
    payment_method = serializers.ChoiceField(
        choices=['cash', 'bank_transfer', 'cheque', 'online', 'card', 'other'],
        required=False,
        write_only=True,
    )

    class Meta:
        model = Invoice
        fields = [
            'client', 'project', 'amount', 'invoice_date', 'due_date', 'notes', 'payment_method'
        ]

    def create(self, validated_data):
        payment_method = validated_data.pop('payment_method', None)
        invoice = Invoice.objects.create(**validated_data)

        if payment_method:
            Payment.objects.create(
                invoice=invoice,
                client=invoice.client,
                project=invoice.project,
                amount=invoice.amount,
                payment_method=payment_method,
                payment_date=invoice.invoice_date,
                created_by=self.context['request'].user if self.context.get('request') else None,
            )

        return invoice


class PaymentSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    remaining_after = serializers.SerializerMethodField()
    invoice_total = serializers.SerializerMethodField()
    invoice_paid = serializers.SerializerMethodField()
    invoice_status = serializers.CharField(source='invoice.status', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'invoice', 'invoice_number', 'client', 'client_name',
            'project', 'project_name', 'amount', 'payment_method', 'payment_date',
            'transaction_reference', 'notes', 'created_at', 'created_by',
            'remaining_after', 'invoice_total', 'invoice_paid', 'invoice_status'
        ]
        read_only_fields = ['payment_id', 'client', 'project', 'created_at', 'created_by']

    def get_remaining_after(self, obj):
        if obj.invoice:
            return float(obj.invoice.remaining_amount)
        return 0

    def get_invoice_total(self, obj):
        if obj.invoice:
            return float(obj.invoice.amount)
        return 0

    def get_invoice_paid(self, obj):
        if obj.invoice:
            return float(obj.invoice.amount_paid)
        return 0


class ClientLedgerSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    payment_id_display = serializers.CharField(source='payment.payment_id', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)

    class Meta:
        model = ClientLedger
        fields = [
            'id', 'client', 'client_name', 'project', 'project_name',
            'invoice', 'invoice_number', 'payment', 'payment_id_display',
            'transaction_type', 'transaction_type_display', 'description',
            'debit', 'credit', 'running_balance', 'transaction_date', 'created_at'
        ]
        read_only_fields = fields


class ClientBalanceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    payment_percentage = serializers.SerializerMethodField()

    class Meta:
        model = ClientBalance
        fields = [
            'id', 'client', 'client_name', 'opening_balance',
            'total_projects_cost', 'total_paid', 'pending_balance',
            'payment_percentage', 'last_updated'
        ]
        read_only_fields = ['last_updated']

    def get_payment_percentage(self, obj):
        if obj.total_projects_cost > 0:
            return round((float(obj.total_paid) / float(obj.total_projects_cost)) * 100, 2)
        return 0


class ClientLedgerDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for client ledger page with all info"""
    ledger_entries = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    invoices = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    payment_percentage = serializers.SerializerMethodField()

    class Meta:
        model = ClientBalance
        fields = [
            'client', 'client_name', 'total_projects_cost', 'total_paid',
            'pending_balance', 'payment_percentage', 'last_updated',
            'ledger_entries', 'balance', 'invoices', 'payments'
        ]

    client_name = serializers.CharField(source='client.name', read_only=True)

    def get_payment_percentage(self, obj):
        if obj.total_projects_cost > 0:
            return round((float(obj.total_paid) / float(obj.total_projects_cost)) * 100, 2)
        return 0

    def get_ledger_entries(self, obj):
        entries = ClientLedger.objects.filter(client=obj.client).order_by('-transaction_date', '-created_at')
        return ClientLedgerSerializer(entries, many=True).data

    def get_balance(self, obj):
        return {
            'total_projects_cost': float(obj.total_projects_cost),
            'total_paid': float(obj.total_paid),
            'pending_balance': float(obj.pending_balance),
            'payment_percentage': self.get_payment_percentage(obj),
        }

    def get_invoices(self, obj):
        invoices = Invoice.objects.filter(client=obj.client).order_by('-invoice_date')
        return InvoiceSerializer(invoices, many=True).data

    def get_payments(self, obj):
        payments = Payment.objects.filter(client=obj.client).order_by('-payment_date')
        return PaymentSerializer(payments, many=True).data


class RevenueSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Revenue
        fields = ['id', 'revenue_id', 'client', 'client_name', 'project',
                  'project_name', 'amount', 'revenue_date', 'description', 'created_at']
        read_only_fields = ['revenue_id', 'created_at']


class CompanyRevenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyRevenue
        fields = [
            'id', 'revenue_id', 'date', 'total_revenue', 'total_expenses',
            'net_profit', 'total_clients', 'total_projects',
            'active_projects', 'total_employees', 'updated_at'
        ]
        read_only_fields = ['revenue_id', 'updated_at']
