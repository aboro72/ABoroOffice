from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContractViewSet, ContractVersionViewSet


app_name = 'contracts_api'

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r'contracts', ContractViewSet, basename='contracts')
router.register(r'versions', ContractVersionViewSet, basename='contract_versions')

urlpatterns = [
    path('', include(router.urls)),
]
