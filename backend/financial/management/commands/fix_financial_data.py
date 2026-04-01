from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from financial.models import Invoice, Revenue, ClientBalance, CompanyRevenue
from client_management.models import Client, Project

class Command(BaseCommand):
    help = 'Fix financial data - recalculate all balances and revenues'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("🔧 Starting financial data fix..."))
        
        # 1. Delete all existing revenues
        self.stdout.write("\n📝 Step 1: Clearing existing revenue records...")
        revenue_count = Revenue.objects.count()
        Revenue.objects.all().delete()
        self.stdout.write(f"   ✅ Deleted {revenue_count} revenue records")
        
        # 2. Recreate revenues from invoices
        self.stdout.write("\n💰 Step 2: Recreating revenues from invoices...")
        invoices = Invoice.objects.all()
        revenue_created = 0
        
        for invoice in invoices:
            revenue, created = Revenue.objects.get_or_create(
                invoice=invoice,
                defaults={
                    'client': invoice.client,
                    'project': invoice.project,
                    'amount': invoice.amount,
                    'revenue_date': invoice.invoice_date,
                    'description': f"Payment received for {invoice.project.name} - Invoice {invoice.invoice_id}"
                }
            )
            if created:
                revenue_created += 1
                self.stdout.write(f"   ✅ Created revenue for {invoice.invoice_id}: ${invoice.amount}")
        
        self.stdout.write(f"   ✅ Created {revenue_created} new revenue records")
        
        # 3. Update client balances
        self.stdout.write("\n👥 Step 3: Updating client balances...")
        for client in Client.objects.all():
            total_paid = Invoice.objects.filter(
                client=client
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            total_projects_cost = Project.objects.filter(
                client=client
            ).aggregate(total=Sum('budget'))['total'] or Decimal('0.00')
            
            balance, created = ClientBalance.objects.update_or_create(
                client=client,
                defaults={
                    'opening_balance': Decimal('0.00'),
                    'total_invoiced': total_paid,
                    'total_projects_cost': total_projects_cost,
                    'pending_balance': total_projects_cost - total_paid
                }
            )
            
            payment_percentage = (total_paid / total_projects_cost * 100) if total_projects_cost > 0 else 0
            self.stdout.write(f"   ✅ {client.name}: Paid ${total_paid} / ${total_projects_cost} ({payment_percentage:.1f}%)")
        
        # 4. Update company revenue for all dates
        self.stdout.write("\n🏢 Step 4: Updating company revenue records...")
        
        # Get all dates with invoices or revenue
        all_dates = set()
        
        # Add dates from invoices
        for invoice in invoices:
            all_dates.add(invoice.invoice_date)
        
        # Add today's date
        all_dates.add(timezone.now().date())
        
        # Add dates from last 30 days if no invoices
        today = timezone.now().date()
        for i in range(30):
            all_dates.add(today - timezone.timedelta(days=i))
        
        # Update company revenue for each date
        for date in sorted(all_dates):
            total_revenue = Revenue.objects.filter(
                revenue_date=date
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            company_revenue, created = CompanyRevenue.objects.update_or_create(
                date=date,
                defaults={
                    'total_revenue': total_revenue,
                    'total_clients': Client.objects.filter(status='active').count(),
                    'total_projects': Project.objects.count(),
                    'active_projects': Project.objects.filter(status='in_progress').count(),
                }
            )
            
            status = "Created" if created else "Updated"
            self.stdout.write(f"   ✅ {status} revenue for {date}: ${total_revenue}")
        
        # 5. Summary
        self.stdout.write("\n📊 SUMMARY:")
        total_company_revenue = Revenue.objects.aggregate(total=Sum('amount'))['total'] or 0
        total_pending = ClientBalance.objects.aggregate(total=Sum('pending_balance'))['total'] or 0
        total_clients = Client.objects.count()
        total_projects = Project.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Financial data fixed successfully!"))
        self.stdout.write(f"\n📈 FINANCIAL SUMMARY:")
        self.stdout.write(f"   💰 Total Company Revenue: ${total_company_revenue:,.2f}")
        self.stdout.write(f"   💸 Total Pending Payments: ${total_pending:,.2f}")
        self.stdout.write(f"   👥 Total Clients: {total_clients}")
        self.stdout.write(f"   📁 Total Projects: {total_projects}")
        
        # Check if revenue matches invoices
        total_invoices = Invoice.objects.aggregate(total=Sum('amount'))['total'] or 0
        if total_company_revenue != total_invoices:
            self.stdout.write(self.style.WARNING(f"\n⚠️ Warning: Revenue (${total_company_revenue}) doesn't match Invoices (${total_invoices})"))
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✅ Revenue matches Invoices: ${total_company_revenue}"))