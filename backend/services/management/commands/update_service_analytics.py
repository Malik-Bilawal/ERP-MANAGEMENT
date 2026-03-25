from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from services.models import ServiceCategory, ServiceCategoryAnalytics
from django.db.models import Sum, Count
from decimal import Decimal

class Command(BaseCommand):
    help = 'Update service category analytics'
    
    def handle(self, *args, **options):
        current_month = timezone.now().date().replace(day=1)
        
        for category in ServiceCategory.objects.filter(is_active=True):
            # Calculate analytics for current month
            analytics, created = ServiceCategoryAnalytics.objects.get_or_create(
                service_category=category,
                month=current_month
            )
            
            # This would need to be connected to your invoice/project models
            # For now, we'll set placeholder values
            analytics.total_revenue = Decimal('0.00')
            analytics.total_clients = 0
            analytics.total_projects = 0
            analytics.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Updated analytics for {category.name}')
            )