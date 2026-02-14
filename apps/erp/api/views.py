from django.db import models
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
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
from .serializers import (
    CustomerSerializer,
    ProductSerializer,
    ProductCategorySerializer,
    ServiceSerializer,
    WorkOrderSerializer,
    SalesOrderSerializer,
    SalesOrderItemSerializer,
    InvoiceSerializer,
    QuoteSerializer,
    QuoteItemSerializer,
    OrderConfirmationSerializer,
    DunningNoticeSerializer,
    StockReceiptSerializer,
    StockReceiptItemSerializer,
    CourseSerializer,
    EnrollmentSerializer,
)
from .permissions import ErpReadWritePermission
from apps.erp.services.pricing import apply_pricing
from apps.erp.services.competitor import get_provider


class BaseErpViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ErpReadWritePermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ['-id']


class CustomerViewSet(BaseErpViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['created_at']


class ProductViewSet(BaseErpViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    search_fields = ['name', 'sku']
    ordering_fields = ['created_at', 'price']


class ServiceViewSet(BaseErpViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    search_fields = ['name']
    ordering_fields = ['created_at', 'hourly_rate']


class WorkOrderViewSet(BaseErpViewSet):
    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'scheduled_for']


class SalesOrderViewSet(BaseErpViewSet):
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    search_fields = []
    ordering_fields = ['created_at', 'total_amount']


class SalesOrderItemViewSet(BaseErpViewSet):
    queryset = SalesOrderItem.objects.all()
    serializer_class = SalesOrderItemSerializer
    search_fields = []
    ordering_fields = ['id']


class InvoiceViewSet(BaseErpViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    search_fields = ['number']
    ordering_fields = ['created_at', 'issue_date', 'total_amount']


class StockReceiptViewSet(BaseErpViewSet):
    queryset = StockReceipt.objects.all()
    serializer_class = StockReceiptSerializer
    search_fields = ['supplier_name']
    ordering_fields = ['created_at', 'receipt_date']


class StockReceiptItemViewSet(BaseErpViewSet):
    queryset = StockReceiptItem.objects.all()
    serializer_class = StockReceiptItemSerializer
    search_fields = []
    ordering_fields = ['id']

    def perform_create(self, serializer):
        item = serializer.save()
        if item.product:
            if item.competitor_price_net is None:
                provider = get_provider()
                if provider:
                    try:
                        fetched = provider.fetch_price(item.product)
                    except Exception:
                        fetched = None
                    if fetched is not None:
                        item.competitor_price_net = fetched
                        item.save(update_fields=['competitor_price_net'])
            update_fields = {
                'stock_qty': models.F('stock_qty') + item.quantity,
                'cost_net': item.unit_cost_net,
            }
            if item.competitor_price_net:
                update_fields['competitor_price_net'] = item.competitor_price_net
            Product.objects.filter(id=item.product_id).update(**update_fields)
            product = Product.objects.get(id=item.product_id)
            apply_pricing(product, cost_net=item.unit_cost_net, competitor_net=item.competitor_price_net)


class CourseViewSet(BaseErpViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    search_fields = ['title']
    ordering_fields = ['created_at', 'start_date']


class EnrollmentViewSet(BaseErpViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    search_fields = []
    ordering_fields = ['created_at']


class ProductCategoryViewSet(BaseErpViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    search_fields = ['name']
    ordering_fields = ['name']


class QuoteViewSet(BaseErpViewSet):
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    search_fields = ['number']
    ordering_fields = ['created_at', 'valid_until', 'total_amount']


class QuoteItemViewSet(BaseErpViewSet):
    queryset = QuoteItem.objects.all()
    serializer_class = QuoteItemSerializer
    search_fields = []
    ordering_fields = ['id']


class OrderConfirmationViewSet(BaseErpViewSet):
    queryset = OrderConfirmation.objects.all()
    serializer_class = OrderConfirmationSerializer
    search_fields = ['number']
    ordering_fields = ['created_at', 'confirmed_at']


class DunningNoticeViewSet(BaseErpViewSet):
    queryset = DunningNotice.objects.all()
    serializer_class = DunningNoticeSerializer
    search_fields = ['number']
    ordering_fields = ['created_at', 'dunning_level']


class CompetitorMockView(APIView):
    permission_classes = []

    def get(self, request):
        from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
        settings_obj = SystemSettings.get_settings()
        api_key = settings_obj.erp_competitor_api_key
        if api_key:
            auth = request.headers.get('Authorization', '')
            if auth != f"Bearer {api_key}":
                return Response({"detail": "Unauthorized"}, status=403)
        q = request.query_params.get('q', '') or ''
        sku = request.query_params.get('sku', '') or ''
        price_param = request.query_params.get('price')
        if price_param:
            try:
                price = float(price_param)
            except Exception:
                price = 99.9
        else:
            seed = len((q + sku).strip())
            price = 49.9 + (seed % 200)
        return Response(
            {
                "price_net": round(price, 2),
                "currency": "EUR",
                "source": "mock",
                "query": q,
                "sku": sku,
            }
        )
