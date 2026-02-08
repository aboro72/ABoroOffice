from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AccountViewSet,
    CostCenterViewSet,
    CostTypeViewSet,
    BusinessPartnerViewSet,
    JournalEntryViewSet,
    JournalLineViewSet,
)

app_name = 'fibu_api'

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r'accounts', AccountViewSet, basename='accounts')
router.register(r'cost-centers', CostCenterViewSet, basename='cost-centers')
router.register(r'cost-types', CostTypeViewSet, basename='cost-types')
router.register(r'partners', BusinessPartnerViewSet, basename='partners')
router.register(r'journal', JournalEntryViewSet, basename='journal')
router.register(r'journal-lines', JournalLineViewSet, basename='journal-lines')

urlpatterns = [
    path('', include(router.urls)),
]
