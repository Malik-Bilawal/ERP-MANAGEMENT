from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from services.models import ServiceCategory, Service, SubService

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed initial services data'
    
    def handle(self, *args, **options):
        # Get or create admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found. Create one first.'))
            return
        
        # Create service categories
        categories = [
            {'name': 'Web Development', 'description': 'Website and web application development services', 'icon': 'web', 'color_code': '#3B82F6'},
            {'name': 'Graphic Design', 'description': 'Graphic design and visual communication services', 'icon': 'brush', 'color_code': '#10B981'},
            {'name': 'Digital Marketing', 'description': 'Digital marketing and SEO services', 'icon': 'campaign', 'color_code': '#F59E0B'},
            {'name': 'Mobile Development', 'description': 'Mobile app development for iOS and Android', 'icon': 'phone_android', 'color_code': '#EF4444'},
            {'name': 'Cloud Services', 'description': 'Cloud infrastructure and DevOps services', 'icon': 'cloud', 'color_code': '#8B5CF6'},
        ]
        
        created_categories = []
        for cat_data in categories:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                    'color_code': cat_data['color_code'],
                    'created_by': admin_user,
                    'is_active': True
                }
            )
            created_categories.append(category)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
        
        # Create services and sub-services
        services_data = {
            'Web Development': {
                'services': [
                    {'name': 'Frontend Development', 'base_price': 5000, 'sub_services': [
                        {'name': 'React.js Development', 'code': 'WEB-REACT-001', 'price': 5000, 'duration': 30},
                        {'name': 'Vue.js Development', 'code': 'WEB-VUE-001', 'price': 4500, 'duration': 25},
                        {'name': 'Angular Development', 'code': 'WEB-ANG-001', 'price': 5500, 'duration': 35},
                    ]},
                    {'name': 'Backend Development', 'base_price': 6000, 'sub_services': [
                        {'name': 'Python/Django API', 'code': 'WEB-DJ-001', 'price': 6000, 'duration': 40},
                        {'name': 'Node.js API', 'code': 'WEB-NODE-001', 'price': 5500, 'duration': 35},
                        {'name': 'PHP/Laravel Development', 'code': 'WEB-LAR-001', 'price': 5000, 'duration': 30},
                    ]},
                    {'name': 'Full Stack Development', 'base_price': 10000, 'sub_services': [
                        {'name': 'E-commerce Website', 'code': 'WEB-ECOMM-001', 'price': 10000, 'duration': 60},
                        {'name': 'Blog Website', 'code': 'WEB-BLOG-001', 'price': 3000, 'duration': 20},
                        {'name': 'Corporate Website', 'code': 'WEB-CORP-001', 'price': 8000, 'duration': 45},
                    ]},
                ]
            },
            'Graphic Design': {
                'services': [
                    {'name': 'Logo Design', 'base_price': 500, 'sub_services': [
                        {'name': 'Simple Logo', 'code': 'GRAPH-SIMP-001', 'price': 300, 'duration': 5},
                        {'name': 'Premium Logo', 'code': 'GRAPH-PREM-001', 'price': 800, 'duration': 10},
                        {'name': 'Corporate Identity', 'code': 'GRAPH-CORP-001', 'price': 1500, 'duration': 15},
                    ]},
                    {'name': 'Branding', 'base_price': 2000, 'sub_services': [
                        {'name': 'Brand Identity Package', 'code': 'GRAPH-BRAND-001', 'price': 2000, 'duration': 20},
                        {'name': 'Business Card Design', 'code': 'GRAPH-CARD-001', 'price': 200, 'duration': 3},
                        {'name': 'Stationery Design', 'code': 'GRAPH-STAT-001', 'price': 500, 'duration': 7},
                    ]},
                ]
            },
            'Digital Marketing': {
                'services': [
                    {'name': 'SEO Services', 'base_price': 1000, 'sub_services': [
                        {'name': 'Basic SEO Package', 'code': 'SEO-BASIC-001', 'price': 1000, 'duration': 30},
                        {'name': 'Advanced SEO', 'code': 'SEO-ADV-001', 'price': 2500, 'duration': 60},
                        {'name': 'Local SEO', 'code': 'SEO-LOCAL-001', 'price': 800, 'duration': 30},
                    ]},
                    {'name': 'Social Media Marketing', 'base_price': 800, 'sub_services': [
                        {'name': 'Facebook Marketing', 'code': 'SMM-FB-001', 'price': 800, 'duration': 30},
                        {'name': 'Instagram Marketing', 'code': 'SMM-IG-001', 'price': 800, 'duration': 30},
                        {'name': 'LinkedIn Marketing', 'code': 'SMM-LI-001', 'price': 1000, 'duration': 30},
                    ]},
                ]
            }
        }
        
        for category in created_categories:
            if category.name in services_data:
                for service_data in services_data[category.name]['services']:
                    service, created = Service.objects.get_or_create(
                        service_category=category,
                        name=service_data['name'],
                        defaults={
                            'description': f"{service_data['name']} services",
                            'base_price': service_data['base_price'],
                            'created_by': admin_user,
                            'is_active': True
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'  Created service: {service.name}'))
                    
                    for sub_data in service_data['sub_services']:
                        sub_service, created = SubService.objects.get_or_create(
                            service=service,
                            code=sub_data['code'],
                            defaults={
                                'name': sub_data['name'],
                                'description': f"{sub_data['name']} service",
                                'price': sub_data['price'],
                                'estimated_duration_days': sub_data['duration'],
                                'created_by': admin_user,
                                'is_active': True
                            }
                        )
                        
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'    Created sub-service: {sub_service.name}'))
        
        self.stdout.write(self.style.SUCCESS('Services data seeded successfully!'))