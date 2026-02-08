from django.urls import path, include
from .views import (
    MarketingHomeView,
    CampaignListView,
    CampaignCreateView,
    CampaignUpdateView,
    CampaignDetailView,
    MarketingKpiTemplateView,
    MarketingKpiExportView,
    MarketingHelpView,
    AssetListView,
    AssetCreateView,
    AssetDetailView,
    AssetUpdateView,
    IdeaListView,
    IdeaCreateView,
    MarketingCalendarView,
)

app_name = 'marketing'

urlpatterns = [
    path('', MarketingHomeView.as_view(), name='home'),
    path('calendar/', MarketingCalendarView.as_view(), name='calendar'),
    path('campaigns/', CampaignListView.as_view(), name='campaign_list'),
    path('campaigns/kpi-template/', MarketingKpiTemplateView.as_view(), name='campaign_kpi_template'),
    path('campaigns/<int:pk>/kpi-export/', MarketingKpiExportView.as_view(), name='campaign_kpi_export'),
    path('campaigns/create/', CampaignCreateView.as_view(), name='campaign_create'),
    path('campaigns/<int:pk>/', CampaignDetailView.as_view(), name='campaign_detail'),
    path('campaigns/<int:pk>/edit/', CampaignUpdateView.as_view(), name='campaign_edit'),
    path('api/', include('apps.marketing.api.urls', namespace='marketing_api')),
    path('assets/', AssetListView.as_view(), name='asset_list'),
    path('assets/create/', AssetCreateView.as_view(), name='asset_create'),
    path('assets/<int:pk>/', AssetDetailView.as_view(), name='asset_detail'),
    path('assets/<int:pk>/edit/', AssetUpdateView.as_view(), name='asset_edit'),
    path('ideas/', IdeaListView.as_view(), name='idea_list'),
    path('ideas/create/', IdeaCreateView.as_view(), name='idea_create'),
    path('help/', MarketingHelpView.as_view(), name='help'),
]

try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
    from rest_framework.permissions import IsAdminUser
except Exception:
    SpectacularAPIView = SpectacularSwaggerView = SpectacularRedocView = None

if SpectacularSwaggerView is not None:
    class MarketingSwaggerView(SpectacularSwaggerView):
        schema = None
        permission_classes = [IsAdminUser]

        def get(self, request, *args, **kwargs):
            response = super().get(request, *args, **kwargs)
            if isinstance(response.data, dict) and 'script_url' not in response.data:
                response.data['script_url'] = None
            return response

    class MarketingSchemaView(SpectacularAPIView):
        permission_classes = [IsAdminUser]

    class MarketingRedocView(SpectacularRedocView):
        permission_classes = [IsAdminUser]

    urlpatterns += [
        path('api/schema/', MarketingSchemaView.as_view(urlconf='apps.marketing.api.urls'), name='marketing-schema'),
        path('api/docs/', MarketingSwaggerView.as_view(url_name='marketing-schema'), name='marketing-swagger'),
        path('api/redoc/', MarketingRedocView.as_view(url_name='marketing-schema'), name='marketing-redoc'),
    ]
