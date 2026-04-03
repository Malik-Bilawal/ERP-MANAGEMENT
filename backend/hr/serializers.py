from rest_framework import serializers
from .models import (
    EmployeeRole, Employee, SalaryRecord, SalaryPayment,
    MonthlyExpensePlan, ExpenseCategory, ActualExpense
)


class EmployeeRoleSerializer(serializers.ModelSerializer):
    employees_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeRole
        fields = [
            'id', 'role_name', 'description', 'is_active',
            'employees_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_employees_count(self, obj):
        return obj.employees.filter(is_active=True).count()


class EmployeeSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.role_name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    salary_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'user', 'first_name', 'last_name',
            'full_name', 'email', 'phone', 'role', 'role_name',
            'employment_type', 'salary', 'salary_display',
            'bank_name', 'account_number', 'ifsc_code',
            'joining_date', 'is_active',
            'emergency_contact_name', 'emergency_contact_phone',
            'address', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'employee_id', 'created_at', 'updated_at']
    
    def get_salary_display(self, obj):
        return f"${obj.salary:,.2f}"


class EmployeeListSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.role_name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'email', 'role_name',
            'employment_type', 'salary', 'joining_date', 'is_active'
        ]


class EmployeeDetailSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.role_name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    salary_summary = serializers.SerializerMethodField()
    unpaid_months_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'user', 'first_name', 'last_name',
            'full_name', 'email', 'phone', 'role', 'role_name',
            'employment_type', 'salary', 'joining_date', 'is_active',
            'bank_name', 'account_number', 'ifsc_code',
            'emergency_contact_name', 'emergency_contact_phone',
            'address', 'notes', 'salary_summary', 'unpaid_months_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'employee_id', 'created_at', 'updated_at']
    
    def get_salary_summary(self, obj):
        return obj.get_salary_summary()
    
    def get_unpaid_months_count(self, obj):
        return len(obj.get_unpaid_months())


class SalaryRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    month_display = serializers.SerializerMethodField()
    
    class Meta:
        model = SalaryRecord
        fields = [
            'id', 'employee', 'employee_name', 'employee_id',
            'month', 'month_display', 'base_salary', 'bonus',
            'deductions', 'net_salary', 'is_paid', 'payment_date',
            'salary_payment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'net_salary', 'created_at', 'updated_at']
    
    def get_month_display(self, obj):
        return obj.month.strftime('%B %Y')
    
    def validate(self, data):
        if data.get('deductions', 0) > data.get('base_salary', 0) + data.get('bonus', 0):
            raise serializers.ValidationError("Deductions cannot exceed base salary plus bonus.")
        return data


class SalaryRecordListSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    month_display = serializers.SerializerMethodField()
    
    class Meta:
        model = SalaryRecord
        fields = [
            'id', 'employee_id', 'employee_name', 'month', 'month_display',
            'base_salary', 'bonus', 'deductions', 'net_salary', 'is_paid', 'payment_date'
        ]


class SalaryPaymentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    month_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = SalaryPayment
        fields = [
            'id', 'payment_id', 'employee', 'employee_name', 'employee_id',
            'amount', 'month', 'month_display', 'status', 'status_display',
            'payment_method', 'payment_method_display', 'payment_date',
            'transaction_reference', 'notes', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'payment_id', 'created_at', 'updated_at']
    
    def get_month_display(self, obj):
        return obj.month.strftime('%B %Y')
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
    
    def validate(self, data):
        if data.get('status') == 'completed' and not data.get('payment_date'):
            data['payment_date'] = self.context['request'].user if self.context.get('request') else None
        return data


class SalaryPaymentListSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    month_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SalaryPayment
        fields = [
            'id', 'payment_id', 'employee_id', 'employee_name',
            'amount', 'month', 'month_display', 'status', 'status_display',
            'payment_method', 'payment_date'
        ]


class MonthlyExpensePlanSerializer(serializers.ModelSerializer):
    month_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    actual_expenses = serializers.SerializerMethodField()
    remaining_budget = serializers.ReadOnlyField()
    utilization_percentage = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = MonthlyExpensePlan
        fields = [
            'id', 'plan_id', 'month', 'month_display',
            'planned_salary', 'planned_bonus', 'planned_medical',
            'planned_travel', 'planned_equipment', 'planned_training',
            'planned_other', 'total_planned',
            'status', 'status_display', 'actual_expenses',
            'remaining_budget', 'utilization_percentage',
            'notes', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'plan_id', 'created_at', 'updated_at']
    
    def get_month_display(self, obj):
        return obj.month.strftime('%B %Y')
    
    def get_actual_expenses(self, obj):
        expenses = obj.actual_expenses
        return {
            'salary': float(expenses['salary']),
            'bonus': float(expenses['bonus']),
            'medical': float(expenses['medical']),
            'travel': float(expenses['travel']),
            'equipment': float(expenses['equipment']),
            'training': float(expenses['training']),
            'other': float(expenses['other']),
            'total': float(expenses['total'])
        }


class MonthlyExpensePlanListSerializer(serializers.ModelSerializer):
    month_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MonthlyExpensePlan
        fields = [
            'id', 'plan_id', 'month', 'month_display',
            'total_planned', 'status', 'status_display',
            'created_at'
        ]
    
    def get_month_display(self, obj):
        return obj.month.strftime('%B %Y')


class ExpenseCategorySerializer(serializers.ModelSerializer):
    expenses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpenseCategory
        fields = [
            'id', 'name', 'expense_type', 'description',
            'is_active', 'expenses_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_expenses_count(self, obj):
        return obj.expenses.filter(status='completed').count()


class ActualExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    expense_type = serializers.CharField(source='category.expense_type', read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True, allow_null=True)
    expense_month_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ActualExpense
        fields = [
            'id', 'expense_id', 'expense_month', 'expense_month_display',
            'category', 'category_name', 'expense_type',
            'amount', 'description', 'status', 'status_display',
            'expense_date', 'employee', 'employee_name',
            'receipt', 'transaction_reference', 'notes',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'expense_id', 'created_at', 'updated_at']
    
    def get_expense_month_display(self, obj):
        return obj.expense_month.strftime('%B %Y')
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class ActualExpenseListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ActualExpense
        fields = [
            'id', 'expense_id', 'category_name', 'amount',
            'status', 'status_display', 'expense_date', 'employee_name'
        ]


class SalaryGenerateSerializer(serializers.Serializer):
    month = serializers.DateField(help_text="First day of the month (e.g., 2024-01-01)")
    include_inactive = serializers.BooleanField(default=False, required=False)
    
    def validate_month(self, value):
        if value.day != 1:
            raise serializers.ValidationError("Month must be the first day of the month.")
        return value


class SalaryBulkProcessSerializer(serializers.Serializer):
    payment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of SalaryPayment IDs to process"
    )
    new_status = serializers.ChoiceField(choices=['processing', 'completed', 'cancelled'])
    payment_method = serializers.ChoiceField(
        choices=['bank_transfer', 'cash', 'cheque', 'online'],
        required=False
    )
    payment_date = serializers.DateField(required=False)
    
    def validate(self, data):
        if data['new_status'] == 'completed' and not data.get('payment_date'):
            raise serializers.ValidationError("Payment date is required when marking as completed.")
        return data


class MonthlyPlanAutoCalculateSerializer(serializers.Serializer):
    month = serializers.DateField(help_text="First day of the month to auto-calculate")
    
    def validate_month(self, value):
        if value.day != 1:
            raise serializers.ValidationError("Month must be the first day of the month.")
        return value
