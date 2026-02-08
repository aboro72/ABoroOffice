from rest_framework import serializers
from apps.marketing.models import (
    Campaign,
    ContentAsset,
    ContentIdea,
    ContentApproval,
    ContentRevision,
    CampaignKpiSnapshot,
)


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            'id',
            'name',
            'objective',
            'status',
            'start_date',
            'end_date',
            'owner',
            'kpi_impressions',
            'kpi_clicks',
            'kpi_conversions',
            'kpi_spend',
            'kpi_revenue',
            'last_kpi_impressions',
            'last_kpi_clicks',
            'last_kpi_conversions',
            'last_kpi_spend',
            'last_kpi_revenue',
            'last_kpi_imported_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_kpi_imported_at']


class ContentAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentAsset
        fields = [
            'id',
            'title',
            'asset_type',
            'channel',
            'campaign',
            'brief',
            'content',
            'status',
            'scheduled_at',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ContentIdeaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentIdea
        fields = [
            'id',
            'title',
            'description',
            'target_audience',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['created_at']


class ContentApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentApproval
        fields = [
            'id',
            'asset',
            'requested_by',
            'reviewed_by',
            'status',
            'note',
            'created_at',
            'reviewed_at',
        ]
        read_only_fields = ['created_at', 'reviewed_at']


class ContentRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentRevision
        fields = [
            'id',
            'asset',
            'title',
            'content',
            'action',
            'note',
            'stamped_by',
            'stamped_at',
        ]
        read_only_fields = ['stamped_at']


class CampaignKpiSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignKpiSnapshot
        fields = [
            'id',
            'campaign',
            'impressions',
            'clicks',
            'conversions',
            'spend',
            'revenue',
            'imported_at',
        ]
        read_only_fields = ['imported_at']
