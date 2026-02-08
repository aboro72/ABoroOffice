from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from apps.marketing.models import (
    Campaign,
    ContentAsset,
    ContentIdea,
    ContentApproval,
    ContentRevision,
    CampaignKpiSnapshot,
)
from .serializers import (
    CampaignSerializer,
    ContentAssetSerializer,
    ContentIdeaSerializer,
    ContentApprovalSerializer,
    ContentRevisionSerializer,
    CampaignKpiSnapshotSerializer,
)
from .permissions import MarketingReadWritePermission


class BaseMarketingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, MarketingReadWritePermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ['-updated_at']


class CampaignViewSet(BaseMarketingViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    search_fields = ['name', 'objective']
    ordering_fields = ['updated_at', 'created_at', 'start_date', 'end_date']


class ContentAssetViewSet(BaseMarketingViewSet):
    queryset = ContentAsset.objects.select_related('campaign').all()
    serializer_class = ContentAssetSerializer
    search_fields = ['title', 'channel', 'content']
    ordering_fields = ['updated_at', 'created_at', 'scheduled_at']

    def get_queryset(self):
        qs = super().get_queryset()
        campaign_id = self.request.query_params.get('campaign')
        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)
        return qs


class ContentIdeaViewSet(BaseMarketingViewSet):
    queryset = ContentIdea.objects.all()
    serializer_class = ContentIdeaSerializer
    search_fields = ['title', 'description', 'target_audience']
    ordering_fields = ['created_at']


class ContentApprovalViewSet(BaseMarketingViewSet):
    queryset = ContentApproval.objects.select_related('asset').all()
    serializer_class = ContentApprovalSerializer
    search_fields = ['note']
    ordering_fields = ['created_at', 'reviewed_at']

    def get_queryset(self):
        qs = super().get_queryset()
        asset_id = self.request.query_params.get('asset')
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs


class ContentRevisionViewSet(BaseMarketingViewSet):
    queryset = ContentRevision.objects.select_related('asset').all()
    serializer_class = ContentRevisionSerializer
    search_fields = ['title', 'note']
    ordering_fields = ['stamped_at']

    def get_queryset(self):
        qs = super().get_queryset()
        asset_id = self.request.query_params.get('asset')
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs


class CampaignKpiSnapshotViewSet(BaseMarketingViewSet):
    queryset = CampaignKpiSnapshot.objects.select_related('campaign').all()
    serializer_class = CampaignKpiSnapshotSerializer
    search_fields = []
    ordering_fields = ['imported_at']

    def get_queryset(self):
        qs = super().get_queryset()
        campaign_id = self.request.query_params.get('campaign')
        if campaign_id:
            qs = qs.filter(campaign_id=campaign_id)
        return qs
