from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from client_management.models import Client, Project
from services.models import SubService
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed sample clients and projects'
    
    def handle(self, *args, **options):
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found'))
            return
        
        # Create sample clients
        sample_clients = [
            {
                'name': 'Tech Solutions Inc',
                'email': 'contact@techsolutions.com',
                'phone': '+92 300 1234567',
                'client_type': 'enterprise',
                'company_name': 'Tech Solutions Inc',
                'industry': 'Technology',
                'billing_address': '123 Tech Plaza, Karachi',
                'city': 'Karachi',
                'state': 'Sindh',
                'postal_code': '75100',
                'primary_contact_name': 'John Doe',
                'status': 'active',
            },
            {
                'name': 'Creative Agency',
                'email': 'info@creativeagency.com',
                'phone': '+92 321 7654321',
                'client_type': 'business',
                'company_name': 'Creative Agency',
                'industry': 'Marketing',
                'billing_address': '45 Creative Street, Lahore',
                'city': 'Lahore',
                'state': 'Punjab',
                'postal_code': '54000',
                'primary_contact_name': 'Sarah Ahmed',
                'status': 'active',
            },
            {
                'name': 'Startup Ventures',
                'email': 'hello@startupventures.com',
                'phone': '+92 345 9876543',
                'client_type': 'startup',
                'company_name': 'Startup Ventures',
                'industry': 'Technology',
                'billing_address': '789 Startup Hub, Islamabad',
                'city': 'Islamabad',
                'state': 'ICT',
                'postal_code': '44000',
                'primary_contact_name': 'Ali Raza',
                'status': 'active',
            },
        ]
        
        for client_data in sample_clients:
            client, created = Client.objects.get_or_create(
                email=client_data['email'],
                defaults={**client_data, 'created_by': admin_user, 'assigned_to': admin_user}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created client: {client.name}'))
                
                # Create sample project for each client
                project = Project.objects.create(
                    client=client,
                    name=f"{client.name} - Website Development",
                    description="Complete website development project",
                    project_type='fixed',
                    budget=5000.00,
                    start_date=timezone.now().date(),
                    estimated_end_date=timezone.now().date() + timezone.timedelta(days=60),
                    project_manager=admin_user,
                    created_by=admin_user,
                    status='planning',
                    priority='high'
                )
                self.stdout.write(self.style.SUCCESS(f'  Created project: {project.name}'))
        
        self.stdout.write(self.style.SUCCESS('Sample data seeded successfully!'))