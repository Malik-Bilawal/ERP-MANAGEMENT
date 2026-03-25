from django.core.management.base import BaseCommand
from django.utils import timezone
from financial.models import FinancialSummary
from django.db.models import Sum
from client_management.models import Client, Project
from financial.models import Invoice, Payment, Expense, Revenue
class Command(BaseCommand):
    help = 'Update daily financial summary'
    
    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Calculate totals
        total_revenue = Revenue.objects.filter(
            revenue_date=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_paid = Payment.objects.filter(
            payment_date=today,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        pending_payments = Invoice.objects.filter(
            status__in=['sent', 'partial']
        ).aggregate(total=Sum('balance_due'))['total'] or 0
        
        total_expenses = Expense.objects.filter(
            expense_date=today,
            status='approved'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Create or update summary
        summary, created = FinancialSummary.objects.update_or_create(
            summary_date=today,
            defaults={
                'total_revenue': total_revenue,
                'total_paid': total_paid,
                'pending_payments': pending_payments,
                'total_expenses': total_expenses,
                'net_profit': total_revenue - total_expenses,
                'total_invoices': Invoice.objects.filter(invoice_date=today).count(),
                'total_payments': Payment.objects.filter(payment_date=today).count(),
                'total_clients': Client.objects.count(),
                'active_projects': Project.objects.filter(status='in_progress').count(),
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Financial summary updated for {today}')
        )