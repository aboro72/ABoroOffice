from rest_framework import viewsets, filters
from apps.contracts.models import Contract, ContractVersion
from .serializers import ContractSerializer, ContractVersionSerializer
from apps.contracts.permissions import can_view_contracts, can_edit_contracts
from rest_framework.permissions import BasePermission, SAFE_METHODS


class ContractsReadWritePermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return can_view_contracts(request.user)
        return can_edit_contracts(request.user)


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all().order_by('-updated_at')
    serializer_class = ContractSerializer
    permission_classes = [ContractsReadWritePermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'counterparty', 'notes']
    ordering_fields = ['updated_at', 'created_at', 'value_eur']
    ordering = ['-updated_at']


class ContractVersionViewSet(viewsets.ModelViewSet):
    queryset = ContractVersion.objects.select_related('contract').all().order_by('-uploaded_at')
    serializer_class = ContractVersionSerializer
    permission_classes = [ContractsReadWritePermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['label', 'summary']
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']
