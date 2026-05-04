"""Deep Test for Invoice/Payment Financial Flow"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ism_project.settings')
import django
django.setup()
from decimal import Decimal
from datetime import date
from client_management.models import Client, Project
from financial.models import Invoice, Payment, ClientLedger, ClientBalance

def test(name, condition, msg=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}")
    if not condition:
        print(f"       {msg}")

def print_balances():
    print("\n" + "=" * 70)
    print("CLIENT BALANCES")
    print("=" * 70)
    for cb in ClientBalance.objects.select_related('client').all():
        print(f"  {cb.client.name:25} | Invoiced: {cb.total_projects_cost:>10} | Paid: {cb.total_paid:>10} | Pending: {cb.pending_balance:>10}")
    print()

def print_ledger(client_name):
    print("\n" + "-" * 70)
    print(f"LEDGER: {client_name}")
    print("-" * 70)
    client = Client.objects.get(name=client_name)
    for entry in ClientLedger.objects.filter(client=client).order_by('transaction_date', 'created_at'):
        print(f"  {entry.transaction_type:12} | Dr: {entry.debit:>10} | Cr: {entry.credit:>10} | Bal: {entry.running_balance:>10}")

def print_invoices(client_name):
    print("\n" + "-" * 70)
    print(f"INVOICES: {client_name}")
    print("-" * 70)
    client = Client.objects.get(name=client_name)
    for inv in Invoice.objects.filter(client=client).order_by('invoice_date'):
        print(f"  {inv.invoice_id:20} | Amt: {inv.amount:>10} | Paid: {inv.amount_paid:>10} | Status: {inv.status}")
        for pay in inv.payments.all():
            print(f"    PAY: {pay.payment_id:20} | {pay.amount:>10}")

print("\n" + "=" * 70)
print("DEEP INVOICE/PAYMENT TEST")
print("=" * 70)

print("\n[1] Cleanup test data...")
Invoice.objects.filter(invoice_id__startswith='TEST-').delete()
Payment.objects.filter(payment_id__startswith='TEST-').delete()
for c in Client.objects.filter(name='Test Client Deep'):
    ClientLedger.objects.filter(client=c).delete()
    c.delete()
print("  Done!")

print("\n[2] Creating test client...")
test_client = Client.objects.create(
    name='Test Client Deep',
    email='test@deep.com',
    client_type='business',
    status='active'
)
test_project = Project.objects.create(
    client=test_client,
    name='Test Project Deep',
    budget=Decimal('100000.00'),
    status='in_progress',
    priority=1,
    start_date=date(2026, 1, 1),
    estimated_end_date=date(2026, 12, 31)
)
print(f"  Created: {test_client.name} | Project: {test_project.name} (${test_project.budget:,.2f})")

# TEST 1: CREATE FIRST INVOICE
print("\n[3] TEST 1: Creating first invoice ($20,000)...")
inv1 = Invoice.objects.create(
    client=test_client,
    project=test_project,
    amount=Decimal('20000.00'),
    invoice_date=date(2026, 2, 1),
)
print_balances()
print_ledger(test_client.name)
print_invoices(test_client.name)
balance = ClientBalance.objects.get(client=test_client)
test("Invoice created", inv1.amount == Decimal('20000.00'), f"Expected $20,000, got ${inv1.amount}")
test("Pending balance = 20000", balance.pending_balance == Decimal('20000.00'), f"Expected $20,000, got ${balance.pending_balance}")

# TEST 2: CREATE PAYMENT FOR INVOICE
print("\n[4] TEST 2: Creating payment ($10,000) for invoice...")
pay1 = Payment.objects.create(
    invoice=inv1,
    client=test_client,
    project=test_project,
    amount=Decimal('10000.00'),
    payment_method='bank_transfer',
    payment_date=date(2026, 2, 15),
)
inv1.refresh_from_db()
balance = ClientBalance.objects.get(client=test_client)
print_balances()
print_ledger(test_client.name)
test("Invoice amount_paid updated", inv1.amount_paid == Decimal('10000.00'), f"Expected $10,000, got ${inv1.amount_paid}")
test("Invoice status = partial", inv1.status == 'partial', f"Expected 'partial', got '{inv1.status}'")
test("Client pending = 10000", balance.pending_balance == Decimal('10000.00'), f"Expected $10,000, got ${balance.pending_balance}")
test("Client total_paid = 10000", balance.total_paid == Decimal('10000.00'), f"Expected $10,000, got ${balance.total_paid}")

# TEST 3: CREATE SECOND PAYMENT
print("\n[5] TEST 3: Creating second payment ($10,000) to complete invoice...")
pay2 = Payment.objects.create(
    invoice=inv1,
    client=test_client,
    project=test_project,
    amount=Decimal('10000.00'),
    payment_method='bank_transfer',
    payment_date=date(2026, 3, 1),
)
inv1.refresh_from_db()
balance = ClientBalance.objects.get(client=test_client)
print_balances()
print_ledger(test_client.name)
test("Invoice fully paid", inv1.amount_paid == Decimal('20000.00'), f"Expected $20,000, got ${inv1.amount_paid}")
test("Invoice status = paid", inv1.status == 'paid', f"Expected 'paid', got '{inv1.status}'")
test("Client pending = 0", balance.pending_balance == Decimal('0.00'), f"Expected $0, got ${balance.pending_balance}")

# TEST 4: CREATE NEW INVOICE
print("\n[6] TEST 4: Creating new invoice ($15,000) for same client...")
inv2 = Invoice.objects.create(
    client=test_client,
    project=test_project,
    amount=Decimal('15000.00'),
    invoice_date=date(2026, 4, 1),
)
inv2.refresh_from_db()
balance = ClientBalance.objects.get(client=test_client)
print_balances()
print_ledger(test_client.name)
print_invoices(test_client.name)
test("Invoice 2 amount = 15000", inv2.amount == Decimal('15000.00'), f"Expected $15,000, got ${inv2.amount}")
test("Client total invoiced = 35000", balance.total_projects_cost == Decimal('35000.00'), f"Expected $35,000, got ${balance.total_projects_cost}")
test("Client pending = 15000", balance.pending_balance == Decimal('15000.00'), f"Expected $15,000, got ${balance.pending_balance}")

# TEST 5: EDIT INVOICE AMOUNT
print("\n[7] TEST 5: Editing invoice amount ($15,000 -> $20,000)...")
inv2.amount = Decimal('20000.00')
inv2.save()
inv2.refresh_from_db()
balance = ClientBalance.objects.get(client=test_client)
print_balances()
test("Invoice amount updated", inv2.amount == Decimal('20000.00'), f"Expected $20,000, got ${inv2.amount}")
test("Total invoiced updated", balance.total_projects_cost == Decimal('40000.00'), f"Expected $40,000, got ${balance.total_projects_cost}")
test("Pending updated", balance.pending_balance == Decimal('20000.00'), f"Expected $20,000, got ${balance.pending_balance}")

# TEST 6: DELETE PAYMENT
print("\n[8] TEST 6: Deleting first payment...")
pay1.delete()
inv1.refresh_from_db()
balance = ClientBalance.objects.get(client=test_client)
print_balances()
test("Invoice amount_paid reduced", inv1.amount_paid == Decimal('10000.00'), f"Expected $10,000, got ${inv1.amount_paid}")
test("Invoice status = partial", inv1.status == 'partial', f"Expected 'partial', got '{inv1.status}'")

# TEST 7: DELETE INVOICE
print("\n[9] TEST 7: Deleting second invoice...")
inv2_id = inv2.id
inv2.delete()
balance = ClientBalance.objects.get(client=test_client)
print_balances()
test("Invoice deleted", not Invoice.objects.filter(id=inv2_id).exists(), "Invoice still exists!")
test("Total invoiced = 20000", balance.total_projects_cost == Decimal('20000.00'), f"Expected $20,000, got ${balance.total_projects_cost}")
test("Pending = 10000", balance.pending_balance == Decimal('10000.00'), f"Expected $10,000, got ${balance.pending_balance}")

# TEST 8: FINAL CLEANUP
print("\n[10] TEST 8: Final cleanup...")
for inv in Invoice.objects.filter(client=test_client):
    inv.delete()
balance = ClientBalance.objects.get(client=test_client)
test("All invoices deleted", Invoice.objects.filter(client=test_client).count() == 0, f"Still have {Invoice.objects.filter(client=test_client).count()} invoices")
test("Pending = 0", balance.pending_balance == Decimal('0.00'), f"Expected $0, got ${balance.pending_balance}")
test("Total paid = 0", balance.total_paid == Decimal('0.00'), f"Expected $0, got ${balance.total_paid}")

print("\n[11] Cleaning up test data...")
test_project.delete()
test_client.delete()
print("  Done!")

print("\n" + "=" * 70)
print("TEST COMPLETE!")
print("=" * 70)