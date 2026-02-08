from django.urls import path, include
from .views import (
    ErpHomeView,
    CustomerListView,
    CustomerCreateView,
    CustomerUpdateView,
    ProductListView,
    ProductCreateView,
    ProductUpdateView,
    ServiceListView,
    ServiceCreateView,
    ServiceUpdateView,
    WorkOrderListView,
    WorkOrderCreateView,
    WorkOrderUpdateView,
    QuoteListView,
    QuoteCreateView,
    QuoteDetailView,
    SalesOrderListView,
    SalesOrderDetailView,
    SalesOrderCreateView,
    SalesOrderUpdateView,
    OrderConfirmationListView,
    InvoiceListView,
    InvoiceDetailView,
    DunningListView,
    DunningDetailView,
    DunningRunView,
    StockReceiptListView,
    StockReceiptCreateView,
    StockReceiptDetailView,
    CompetitorDebugView,
    CourseListView,
    CourseDetailView,
    CourseCreateView,
    CourseUpdateView,
    ErpHelpView,
    ErpPluginHubView,
    PricingHelpView,
)
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
    from rest_framework.permissions import IsAdminUser
except Exception:
    SpectacularAPIView = SpectacularSwaggerView = SpectacularRedocView = None

app_name = 'erp'

urlpatterns = [
    path('', ErpHomeView.as_view(), name='home'),
    path('customers/', CustomerListView.as_view(), name='customers'),
    path('customers/create/', CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_edit'),
    path('products/', ProductListView.as_view(), name='products'),
    path('products/create/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_edit'),
    path('services/', ServiceListView.as_view(), name='services'),
    path('services/create/', ServiceCreateView.as_view(), name='service_create'),
    path('services/<int:pk>/edit/', ServiceUpdateView.as_view(), name='service_edit'),
    path('workorders/', WorkOrderListView.as_view(), name='workorders'),
    path('workorders/create/', WorkOrderCreateView.as_view(), name='workorder_create'),
    path('workorders/<int:pk>/edit/', WorkOrderUpdateView.as_view(), name='workorder_edit'),
    path('quotes/', QuoteListView.as_view(), name='quotes'),
    path('quotes/create/', QuoteCreateView.as_view(), name='quote_create'),
    path('quotes/<int:pk>/', QuoteDetailView.as_view(), name='quote_detail'),
    path('salesorders/', SalesOrderListView.as_view(), name='salesorders'),
    path('salesorders/create/', SalesOrderCreateView.as_view(), name='salesorder_create'),
    path('salesorders/<int:pk>/', SalesOrderDetailView.as_view(), name='salesorder_detail'),
    path('salesorders/<int:pk>/edit/', SalesOrderUpdateView.as_view(), name='salesorder_edit'),
    path('confirmations/', OrderConfirmationListView.as_view(), name='confirmations'),
    path('invoices/', InvoiceListView.as_view(), name='invoices'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),
    path('dunning/', DunningListView.as_view(), name='dunning'),
    path('dunning/<int:pk>/', DunningDetailView.as_view(), name='dunning_detail'),
    path('dunning/run/', DunningRunView.as_view(), name='dunning_run'),
    path('stock/receipts/', StockReceiptListView.as_view(), name='stockreceipts'),
    path('stock/receipts/create/', StockReceiptCreateView.as_view(), name='stockreceipt_create'),
    path('stock/receipts/<int:pk>/', StockReceiptDetailView.as_view(), name='stockreceipt_detail'),
    path('competitor-debug/', CompetitorDebugView.as_view(), name='competitor_debug'),
    path('courses/', CourseListView.as_view(), name='courses'),
    path('courses/create/', CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:pk>/edit/', CourseUpdateView.as_view(), name='course_edit'),
    path('help/', ErpHelpView.as_view(), name='help'),
    path('pricing-help/', PricingHelpView.as_view(), name='pricing_help'),
    path('plugins/', ErpPluginHubView.as_view(), name='plugins'),
    path('api/', include('apps.erp.api.urls', namespace='erp_api')),
]

if SpectacularSwaggerView is not None:
    class ErpSwaggerView(SpectacularSwaggerView):
        schema = None
        permission_classes = [IsAdminUser]

        def get(self, request, *args, **kwargs):
            response = super().get(request, *args, **kwargs)
            if isinstance(response.data, dict) and 'script_url' not in response.data:
                response.data['script_url'] = None
            return response

    class ErpSchemaView(SpectacularAPIView):
        permission_classes = [IsAdminUser]

    class ErpRedocView(SpectacularRedocView):
        permission_classes = [IsAdminUser]

    urlpatterns += [
        path('api/schema/', ErpSchemaView.as_view(urlconf='apps.erp.api.urls'), name='erp-schema'),
        path('api/docs/', ErpSwaggerView.as_view(url_name='erp:erp-schema'), name='erp-swagger'),
        path('api/redoc/', ErpRedocView.as_view(url_name='erp:erp-schema'), name='erp-redoc'),
    ]
