from rest_framework import serializers
from apps.personnel.models import Instructor, Employee
from apps.erp.models import (
    Customer,
    Product,
    ProductCategory,
    Service,
    WorkOrder,
    SalesOrder,
    SalesOrderItem,
    Invoice,
    Quote,
    QuoteItem,
    OrderConfirmation,
    DunningNotice,
    StockReceipt,
    StockReceiptItem,
    Course,
    Enrollment,
)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'customer_type', 'email', 'phone', 'address', 'created_at']
        read_only_fields = ['created_at']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'sku',
            'price',
            'stock_qty',
            'reorder_level',
            'description',
            'marketing_campaign',
            'created_at',
        ]
        read_only_fields = ['created_at']


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'hourly_rate', 'description', 'created_at']
        read_only_fields = ['created_at']


class WorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = [
            'id',
            'customer',
            'title',
            'description',
            'status',
            'scheduled_for',
            'assigned_to',
            'contract',
            'created_at',
        ]
        read_only_fields = ['created_at']


class SalesOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = [
            'id',
            'customer',
            'status',
            'tax_rate',
            'net_amount',
            'tax_amount',
            'total_amount',
            'contract',
            'created_at',
        ]
        read_only_fields = ['created_at']


class SalesOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrderItem
        fields = ['id', 'order', 'product', 'quantity', 'unit_price']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            'id',
            'order',
            'number',
            'status',
            'issue_date',
            'due_date',
            'billing_name',
            'billing_address',
            'net_amount',
            'tax_rate',
            'tax_amount',
            'total_amount',
            'notes',
            'created_at',
        ]
        read_only_fields = ['created_at']


class StockReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockReceipt
        fields = ['id', 'supplier_name', 'receipt_date', 'invoice_file', 'notes', 'created_at']
        read_only_fields = ['created_at']


class StockReceiptItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockReceiptItem
        fields = ['id', 'receipt', 'product', 'quantity', 'unit_cost_net', 'competitor_price_net']


class CourseSerializer(serializers.ModelSerializer):
    instructors = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Instructor.objects.all(),
        required=False,
    )
    employees = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Employee.objects.all(),
        required=False,
    )

    class Meta:
        model = Course
        fields = [
            'id',
            'event_number',
            'title',
            'customer',
            'instructors',
            'employees',
            'required_skill',
            'work_order',
            'contract',
            'status',
            'instructor_days',
            'instructor_daily_cost',
            'expenses',
            'lodging',
            'mobile_classroom_required',
            'mobile_classroom_product',
            'mobile_classroom_cost',
            'vat_rate',
            'price_net',
            'price_gross',
            'start_date',
            'end_date',
            'capacity',
            'description',
            'created_at',
        ]
        read_only_fields = ['created_at']


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'course', 'customer', 'status', 'created_at']
        read_only_fields = ['created_at']


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description', 'parent']


class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = [
            'id',
            'number',
            'customer',
            'status',
            'valid_until',
            'net_amount',
            'tax_rate',
            'tax_amount',
            'total_amount',
            'notes',
            'created_at',
        ]
        read_only_fields = ['created_at', 'number']


class QuoteItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteItem
        fields = ['id', 'quote', 'product', 'service', 'description', 'quantity', 'unit_price']


class OrderConfirmationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderConfirmation
        fields = [
            'id',
            'number',
            'quote',
            'sales_order',
            'confirmed_at',
            'notes',
            'created_at',
        ]
        read_only_fields = ['created_at', 'number']


class DunningNoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DunningNotice
        fields = [
            'id',
            'number',
            'invoice',
            'dunning_level',
            'dunning_fee',
            'status',
            'sent_at',
            'notes',
            'created_at',
        ]
        read_only_fields = ['created_at', 'number']
