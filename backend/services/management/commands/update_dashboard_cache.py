from django.core.management.base import BaseCommand
from django.utils import timezone
from financial.views import financial_dashboard
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Update dashboard cache'
    
    def handle(self, *args, **options):
        # Clear old cache
        cache.delete('financial_dashboard')
        
        self.stdout.write(self.style.SUCCESS('Dashboard cache cleared!'))