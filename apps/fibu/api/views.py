from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from apps.fibu.models import Account, CostCenter, CostType, BusinessPartner, JournalEntry, JournalLine
from .serializers import (
    AccountSerializer,
    CostCenterSerializer,
    CostTypeSerializer,
    BusinessPartnerSerializer,
    JournalEntrySerializer,
    JournalLineSerializer,
)


class BaseFibuViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]


class AccountViewSet(BaseFibuViewSet):
    queryset = Account.objects.all().order_by('code')
    serializer_class = AccountSerializer
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']


class CostCenterViewSet(BaseFibuViewSet):
    queryset = CostCenter.objects.all().order_by('code')
    serializer_class = CostCenterSerializer
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']


class CostTypeViewSet(BaseFibuViewSet):
    queryset = CostType.objects.all().order_by('code')
    serializer_class = CostTypeSerializer
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']


class BusinessPartnerViewSet(BaseFibuViewSet):
    queryset = BusinessPartner.objects.all().order_by('name')
    serializer_class = BusinessPartnerSerializer
    search_fields = ['name', 'partner_number', 'vat_id']
    ordering_fields = ['name', 'created_at']


class JournalEntryViewSet(BaseFibuViewSet):
    queryset = JournalEntry.objects.all().order_by('-date', '-id')
    serializer_class = JournalEntrySerializer
    search_fields = ['reference', 'description']
    ordering_fields = ['date', 'id']


class JournalLineViewSet(BaseFibuViewSet):
    queryset = JournalLine.objects.all().order_by('-id')
    serializer_class = JournalLineSerializer
    search_fields = ['description']
    ordering_fields = ['id']
