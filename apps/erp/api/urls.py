from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet,
    ProductViewSet,
    ServiceViewSet,
    WorkOrderViewSet,
    SalesOrderViewSet,
    SalesOrderItemViewSet,
    InvoiceViewSet,
    StockReceiptViewSet,
    StockReceiptItemViewSet,
    CourseViewSet,
    EnrollmentViewSet,
    CompetitorMockView,
)

app_name = 'erp_api'

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r'customers', CustomerViewSet, basename='customers')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'services', ServiceViewSet, basename='services')
router.register(r'workorders', WorkOrderViewSet, basename='workorders')
router.register(r'salesorders', SalesOrderViewSet, basename='salesorders')
router.register(r'salesorder-items', SalesOrderItemViewSet, basename='salesorder-items')
router.register(r'invoices', InvoiceViewSet, basename='invoices')
router.register(r'stock-receipts', StockReceiptViewSet, basename='stock-receipts')
router.register(r'stock-receipt-items', StockReceiptItemViewSet, basename='stock-receipt-items')
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollments')

urlpatterns = [
    path('', include(router.urls)),
    path('competitor-mock/', CompetitorMockView.as_view(), name='competitor-mock'),
]
