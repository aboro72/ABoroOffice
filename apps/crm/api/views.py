from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from apps.crm.models import Account, Lead, Opportunity, Activity, Note
from .serializers import (
    AccountSerializer,
    LeadSerializer,
    OpportunitySerializer,
    ActivitySerializer,
    NoteSerializer,
)
from .permissions import CrmReadWritePermission


class BaseCrmViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CrmReadWritePermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ['-updated_at']


class AccountViewSet(BaseCrmViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    search_fields = ['name', 'industry', 'email', 'phone']
    ordering_fields = ['updated_at', 'created_at', 'name']


class LeadViewSet(BaseCrmViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    search_fields = ['name', 'company', 'email', 'phone']
    ordering_fields = ['updated_at', 'created_at', 'score']


class OpportunityViewSet(BaseCrmViewSet):
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    search_fields = ['name']
    ordering_fields = ['updated_at', 'created_at', 'amount']


class ActivityViewSet(BaseCrmViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    search_fields = ['subject']
    ordering_fields = ['created_at', 'due_date']

    def get_queryset(self):
        qs = super().get_queryset()
        lead_id = self.request.query_params.get('lead')
        account_id = self.request.query_params.get('account')
        if lead_id:
            qs = qs.filter(lead_id=lead_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        return qs


class NoteViewSet(BaseCrmViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    search_fields = ['content']
    ordering_fields = ['created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        lead_id = self.request.query_params.get('lead')
        account_id = self.request.query_params.get('account')
        if lead_id:
            qs = qs.filter(lead_id=lead_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        return qs
