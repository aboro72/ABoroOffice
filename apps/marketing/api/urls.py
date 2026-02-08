from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CampaignViewSet,
    ContentAssetViewSet,
    ContentIdeaViewSet,
    ContentApprovalViewSet,
    ContentRevisionViewSet,
    CampaignKpiSnapshotViewSet,
)

app_name = 'marketing_api'

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r'campaigns', CampaignViewSet, basename='campaigns')
router.register(r'assets', ContentAssetViewSet, basename='assets')
router.register(r'ideas', ContentIdeaViewSet, basename='ideas')
router.register(r'approvals', ContentApprovalViewSet, basename='approvals')
router.register(r'revisions', ContentRevisionViewSet, basename='revisions')
router.register(r'kpi-snapshots', CampaignKpiSnapshotViewSet, basename='kpi-snapshots')

urlpatterns = [
    path('', include(router.urls)),
]
