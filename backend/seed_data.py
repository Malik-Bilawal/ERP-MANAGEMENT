"""
Seed script for ISM - Creates realistic test data for Income + Outcome modules
Run: python manage.py shell < backend/seed_data.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from datetime import date
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User
from client_management.models import Client, Project
from services.models import ServiceCategory, Service
from financial.models import Invoice, Payment, Revenue, CompanyRevenue, ClientLedger, ClientBalance
from hr.models import (
    EmployeeRole, Employee, SalaryPayment, SalaryRecord,
    ExpenseCategory, ActualExpense, ProjectAssignment,
    ProjectManager, EmployeeBenefit, EmployeeLedger
)

print("=" * 60)
print("STARTING DATA SEED")
print("=" * 60)

# --- Clean existing data ---
print("\n[1/10] Cleaning existing data...")
EmployeeLedger.objects.all().delete()
EmployeeBenefit.objects.all().delete()
ProjectManager.objects.all().delete()
ProjectAssignment.objects.all().delete()
ActualExpense.objects.all().delete()
SalaryPayment.objects.all().delete()
SalaryRecord.objects.all().delete()
Invoice.objects.all().delete()
Payment.objects.all().delete()
Revenue.objects.all().delete()
ClientLedger.objects.all().delete()
ClientBalance.objects.all().delete()
CompanyRevenue.objects.all().delete()
Project.objects.all().delete()
Client.objects.all().delete()
Employee.objects.all().delete()
EmployeeRole.objects.all().delete()
ExpenseCategory.objects.all().delete()
ServiceCategory.objects.all().delete()
User.objects.filter(username__startswith='seed_').delete()
print("  Done!")

# --- Create Clients ---
print("\n[2/10] Creating clients...")
clients_data = [
    {'name': 'Acme Corporation', 'email': 'contact@acme.com', 'phone': '+1-555-0101', 'client_type': 'business', 'status': 'active'},
    {'name': 'TechStart Inc', 'email': 'info@techstart.io', 'phone': '+1-555-0102', 'client_type': 'startup', 'status': 'active'},
    {'name': 'Global Media Ltd', 'email': 'hello@globalmedia.com', 'phone': '+1-555-0103', 'client_type': 'business', 'status': 'active'},
    {'name': 'DataFlow Systems', 'email': 'support@dataflow.com', 'phone': '+1-555-0104', 'client_type': 'enterprise', 'status': 'active'},
    {'name': 'CloudNine Solutions', 'email': 'admin@cloudnine.io', 'phone': '+1-555-0105', 'client_type': 'business', 'status': 'active'},
]
clients = []
for cd in clients_data:
    c = Client.objects.create(**cd)
    clients.append(c)
    print(f"  Created: {c.name}")

# --- Create Projects ---
print("\n[3/10] Creating projects...")
projects_data = [
    {'client': 0, 'name': 'E-Commerce Platform', 'budget': Decimal('50000.00'), 'status': 'in_progress', 'priority': 1, 'start_date': '2026-01-15', 'estimated_end_date': '2026-06-30'},
    {'client': 0, 'name': 'Mobile App Redesign', 'budget': Decimal('25000.00'), 'status': 'in_progress', 'priority': 2, 'start_date': '2026-02-01', 'estimated_end_date': '2026-05-15'},
    {'client': 1, 'name': 'AI Chatbot Integration', 'budget': Decimal('35000.00'), 'status': 'in_progress', 'priority': 1, 'start_date': '2026-01-20', 'estimated_end_date': '2026-07-31'},
    {'client': 1, 'name': 'Cloud Migration', 'budget': Decimal('20000.00'), 'status': 'planning', 'priority': 2, 'start_date': '2026-03-01', 'estimated_end_date': '2026-08-31'},
    {'client': 2, 'name': 'Video Streaming Platform', 'budget': Decimal('75000.00'), 'status': 'in_progress', 'priority': 1, 'start_date': '2026-01-10', 'estimated_end_date': '2026-09-30'},
    {'client': 2, 'name': 'Content Management System', 'budget': Decimal('30000.00'), 'status': 'in_progress', 'priority': 2, 'start_date': '2026-02-15', 'estimated_end_date': '2026-06-15'},
    {'client': 3, 'name': 'Data Analytics Dashboard', 'budget': Decimal('40000.00'), 'status': 'in_progress', 'priority': 1, 'start_date': '2026-01-25', 'estimated_end_date': '2026-07-15'},
    {'client': 4, 'name': 'SaaS Platform Development', 'budget': Decimal('60000.00'), 'status': 'in_progress', 'priority': 1, 'start_date': '2026-02-01', 'estimated_end_date': '2026-08-31'},
    {'client': 4, 'name': 'API Gateway Setup', 'budget': Decimal('15000.00'), 'status': 'completed', 'priority': 3, 'start_date': '2025-11-01', 'estimated_end_date': '2026-02-28'},
]
projects = []
for pd in projects_data:
    p = Project.objects.create(
        client=clients[pd['client']],
        name=pd['name'],
        budget=pd['budget'],
        status=pd['status'],
        priority=pd['priority'],
        start_date=pd['start_date'],
        estimated_end_date=pd['estimated_end_date'],
        description=f"Project: {pd['name']} for {clients[pd['client']].name}"
    )
    projects.append(p)
    print(f"  Created: {p.name} (${p.budget:,.2f})")

# --- Create Employee Roles ---
print("\n[4/10] Creating employee roles...")
roles_data = ['Senior Developer', 'Full Stack Developer', 'UI/UX Designer', 'Project Manager', 'DevOps Engineer', 'QA Engineer', 'Backend Developer', 'Frontend Developer']
roles = []
for rd in roles_data:
    r = EmployeeRole.objects.create(role_name=rd)
    roles.append(r)
    print(f"  Created: {r.role_name}")

# --- Create Employees ---
print("\n[5/10] Creating employees...")
employees_data = [
    {'first': 'Ahmed', 'last': 'Khan', 'email': 'ahmed.khan@company.com', 'role': 0, 'salary': Decimal('8000.00'), 'type': 'full_time'},
    {'first': 'Sarah', 'last': 'Johnson', 'email': 'sarah.j@company.com', 'role': 1, 'salary': Decimal('7000.00'), 'type': 'full_time'},
    {'first': 'Mike', 'last': 'Chen', 'email': 'mike.chen@company.com', 'role': 2, 'salary': Decimal('6500.00'), 'type': 'full_time'},
    {'first': 'Fatima', 'last': 'Ali', 'email': 'fatima.ali@company.com', 'role': 3, 'salary': Decimal('9000.00'), 'type': 'full_time'},
    {'first': 'David', 'last': 'Wilson', 'email': 'david.w@company.com', 'role': 4, 'salary': Decimal('7500.00'), 'type': 'full_time'},
    {'first': 'Aisha', 'last': 'Patel', 'email': 'aisha.p@company.com', 'role': 5, 'salary': Decimal('6000.00'), 'type': 'full_time'},
    {'first': 'James', 'last': 'Brown', 'email': 'james.b@company.com', 'role': 6, 'salary': Decimal('7200.00'), 'type': 'full_time'},
    {'first': 'Emily', 'last': 'Davis', 'email': 'emily.d@company.com', 'role': 7, 'salary': Decimal('6800.00'), 'type': 'full_time'},
    {'first': 'Omar', 'last': 'Hassan', 'email': 'omar.h@company.com', 'role': 1, 'salary': Decimal('6500.00'), 'type': 'full_time'},
    {'first': 'Lisa', 'last': 'Wang', 'email': 'lisa.w@company.com', 'role': 2, 'salary': Decimal('6200.00'), 'type': 'contract'},
]
employees = []
for i, ed in enumerate(employees_data):
    user = User.objects.create_user(
        username=f'seed_emp{i}',
        email=ed['email'],
        password='emp12345'
    )
    emp = Employee(
        user=user,
        first_name=ed['first'],
        last_name=ed['last'],
        email=ed['email'],
        role=roles[ed['role']],
        employment_type=ed['type'],
        salary=ed['salary'],
        joining_date='2025-06-01',
        bank_name='First National Bank',
        account_number=f'ACC{1000+i}',
    )
    emp.employee_id = f'SEED-EMP-{i+1:04d}'
    emp.save()
    employees.append(emp)
    print(f"  Created: {emp.full_name} (${emp.salary:,.2f}/month)")

# --- Create Project Assignments ---
print("\n[6/10] Creating project assignments...")
assignments_data = [
    (0, 0, 'Lead Developer', 40),
    (1, 0, 'Full Stack Dev', 35),
    (2, 1, 'Senior Dev', 40),
    (3, 1, 'Full Stack Dev', 30),
    (4, 2, 'UI/UX Designer', 35),
    (5, 2, 'Frontend Dev', 40),
    (6, 3, 'Backend Dev', 40),
    (7, 4, 'DevOps Engineer', 40),
    (8, 5, 'QA Engineer', 35),
    (0, 3, 'Project Manager', 20),
    (1, 4, 'Project Manager', 20),
    (2, 5, 'Project Manager', 20),
    (3, 6, 'Backend Dev', 30),
    (4, 7, 'Frontend Dev', 35),
    (5, 8, 'Full Stack Dev', 40),
]
for emp_idx, proj_idx, role, hours in assignments_data:
    pa = ProjectAssignment.objects.create(
        employee=employees[emp_idx],
        project=projects[proj_idx],
        role_on_project=role,
        hours_per_week=hours,
        start_date='2026-01-15',
    )
    print(f"  {employees[emp_idx].full_name} -> {projects[proj_idx].name} ({role}, {hours}h/wk)")

# --- Create Project Managers ---
print("\n[7/10] Creating project managers...")
manager_data = [
    (0, 3),  # Fatima manages project 0
    (1, 3),  # Fatima manages project 1
    (2, 4),  # David manages project 2
    (3, 4),  # David manages project 3
    (4, 5),  # Ahmed manages project 4
    (5, 6),  # Sarah manages project 5
    (6, 7),  # Mike manages project 6
    (7, 8),  # James manages project 7
]
for emp_idx, proj_idx in manager_data:
    pm = ProjectManager.objects.create(
        employee=employees[emp_idx],
        project=projects[proj_idx],
    )
    print(f"  {employees[emp_idx].full_name} manages {projects[proj_idx].name}")

# --- Create Employee Benefits ---
print("\n[8/10] Creating employee benefits...")
benefit_types = ['travel', 'medical', 'training', 'phone', 'equipment']
benefit_limits = {
    'travel': Decimal('3000.00'),
    'medical': Decimal('5000.00'),
    'training': Decimal('2000.00'),
    'phone': Decimal('1200.00'),
    'equipment': Decimal('1500.00'),
}
for emp in employees:
    for btype in benefit_types:
        EmployeeBenefit.objects.create(
            employee=emp,
            benefit_type=btype,
            annual_limit=benefit_limits[btype],
            start_date='2026-01-01',
            end_date='2026-12-31',
            description=f"{btype.capitalize()} benefit for {emp.full_name}",
        )
    print(f"  Benefits created for {emp.full_name}")

# --- Create Invoices ---
print("\n[9/10] Creating invoices and payments...")
invoice_data = [
    (0, 0, Decimal('15000.00'), Decimal('15000.00'), 'full'),
    (0, 1, Decimal('8000.00'), Decimal('8000.00'), 'full'),
    (1, 2, Decimal('12000.00'), Decimal('12000.00'), 'full'),
    (2, 4, Decimal('25000.00'), Decimal('20000.00'), 'partial'),
    (2, 5, Decimal('10000.00'), Decimal('10000.00'), 'full'),
    (3, 6, Decimal('15000.00'), Decimal('15000.00'), 'full'),
    (4, 7, Decimal('20000.00'), Decimal('15000.00'), 'partial'),
]
for client_idx, proj_idx, amount, paid, option in invoice_data:
    inv = Invoice.objects.create(
        client=clients[client_idx],
        project=projects[proj_idx],
        amount=amount,
        amount_paid=paid,
        payment_option=option,
        payment_method='bank_transfer',
        invoice_date=date(2026, 3, 15),
        due_date=date(2026, 4, 15),
    )
    # Create payment record for full/partial paid invoices
    if paid > 0:
        Payment.objects.create(
            invoice=inv,
            client=clients[client_idx],
            project=projects[proj_idx],
            amount=paid,
            payment_method='bank_transfer',
            payment_date=date(2026, 3, 15),
        )
    print(f"  Invoice: {inv.invoice_id} - {clients[client_idx].name} - ${amount:,.2f} ({inv.status})")

# --- Create Salary Payments ---
print("\n[10/10] Creating salary payments and expenses...")
for emp in employees:
    SalaryPayment.objects.create(
        employee=emp,
        amount=emp.salary,
        month=date(2026, 3, 1),
        status='completed',
        payment_method='bank_transfer',
        payment_date=date(2026, 3, 28),
    )
    print(f"  Salary paid: {emp.full_name} - ${emp.salary:,.2f}")

# Create some expenses
expense_cats = [
    ExpenseCategory.objects.create(name='Office Rent', expense_type='other'),
    ExpenseCategory.objects.create(name='Software Licenses', expense_type='equipment'),
    ExpenseCategory.objects.create(name='Team Lunch', expense_type='other'),
    ExpenseCategory.objects.create(name='Travel Expense', expense_type='travel'),
    ExpenseCategory.objects.create(name='Medical Claim', expense_type='medical'),
]

expenses_data = [
    (0, Decimal('5000.00'), 'Monthly office rent', date(2026, 3, 15)),
    (1, Decimal('2000.00'), 'Annual software licenses', date(2026, 3, 10)),
    (2, Decimal('500.00'), 'Team lunch for project launch', date(2026, 3, 20)),
    (3, Decimal('1500.00'), 'Client meeting travel', date(2026, 3, 18)),
    (4, Decimal('800.00'), 'Employee medical claim', date(2026, 3, 22)),
]
for cat_idx, amount, desc, exp_date in expenses_data:
    ActualExpense.objects.create(
        expense_month=date(2026, 3, 1),
        category=expense_cats[cat_idx],
        amount=amount,
        description=desc,
        status='completed',
        expense_date=exp_date,
    )
    print(f"  Expense: {expense_cats[cat_idx].name} - ${amount:,.2f}")

# Update company revenue
CompanyRevenue.update_daily()

print("\n" + "=" * 60)
print("SEED COMPLETE!")
print("=" * 60)
print(f"  Clients: {Client.objects.count()}")
print(f"  Projects: {Project.objects.count()}")
print(f"  Employees: {Employee.objects.count()}")
print(f"  Project Assignments: {ProjectAssignment.objects.count()}")
print(f"  Project Managers: {ProjectManager.objects.count()}")
print(f"  Employee Benefits: {EmployeeBenefit.objects.count()}")
print(f"  Invoices: {Invoice.objects.count()}")
print(f"  Salary Payments: {SalaryPayment.objects.count()}")
print(f"  Expenses: {ActualExpense.objects.count()}")
print(f"  Employee Ledger Entries: {EmployeeLedger.objects.count()}")
print(f"  Company Revenue Records: {CompanyRevenue.objects.count()}")
print("=" * 60)
