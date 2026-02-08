from django.urls import path, include
from .views import (
    CrmHomeView,
    AccountListView,
    AccountDetailView,
    AccountCreateView,
    AccountUpdateView,
    LeadListView,
    LeadDetailView,
    LeadCreateView,
    LeadUpdateView,
    OpportunityListView,
    OpportunityDetailView,
    OpportunityCreateView,
    OpportunityUpdateView,
    OpportunityBoardView,
    EmailTemplateListView,
    EmailTemplateCreateView,
    EmailTemplateUpdateView,
    LeadSourceProfileListView,
    LeadSourceProfileCreateView,
    LeadSourceProfileUpdateView,
    LeadSourceRunView,
    LeadStagingListView,
    LeadStagingNeedsWebsiteView,
    LeadStagingBatchWebsiteUpdateView,
    LeadStagingUpdateView,
    LeadStagingImportView,
    LeadStagingBulkImportView,
    LeadStagingQuickUpdateView,
    CrmHelpView,
)
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
    from rest_framework.permissions import IsAdminUser
except Exception:
    SpectacularAPIView = SpectacularSwaggerView = SpectacularRedocView = None

app_name = 'crm'

urlpatterns = [
    path('', CrmHomeView.as_view(), name='home'),
    path('accounts/', AccountListView.as_view(), name='account_list'),
    path('accounts/create/', AccountCreateView.as_view(), name='account_create'),
    path('accounts/<int:pk>/', AccountDetailView.as_view(), name='account_detail'),
    path('accounts/<int:pk>/edit/', AccountUpdateView.as_view(), name='account_edit'),
    path('leads/', LeadListView.as_view(), name='lead_list'),
    path('leads/create/', LeadCreateView.as_view(), name='lead_create'),
    path('leads/<int:pk>/', LeadDetailView.as_view(), name='lead_detail'),
    path('leads/<int:pk>/edit/', LeadUpdateView.as_view(), name='lead_edit'),
    path('opportunities/', OpportunityListView.as_view(), name='opportunity_list'),
    path('opportunities/create/', OpportunityCreateView.as_view(), name='opportunity_create'),
    path('opportunities/<int:pk>/', OpportunityDetailView.as_view(), name='opportunity_detail'),
    path('opportunities/<int:pk>/edit/', OpportunityUpdateView.as_view(), name='opportunity_edit'),
    path('opportunities/board/', OpportunityBoardView.as_view(), name='opportunity_board'),
    path('email-templates/', EmailTemplateListView.as_view(), name='email_template_list'),
    path('email-templates/create/', EmailTemplateCreateView.as_view(), name='email_template_create'),
    path('email-templates/<int:pk>/edit/', EmailTemplateUpdateView.as_view(), name='email_template_edit'),
    path('sources/', LeadSourceProfileListView.as_view(), name='lead_sources'),
    path('sources/create/', LeadSourceProfileCreateView.as_view(), name='lead_source_create'),
    path('sources/<int:pk>/edit/', LeadSourceProfileUpdateView.as_view(), name='lead_source_edit'),
    path('sources/<int:pk>/run/', LeadSourceRunView.as_view(), name='lead_source_run'),
    path('staging/', LeadStagingListView.as_view(), name='lead_staging'),
    path('staging/needs-website/', LeadStagingNeedsWebsiteView.as_view(), name='lead_staging_needs_website'),
    path('staging/batch-website/', LeadStagingBatchWebsiteUpdateView.as_view(), name='lead_staging_batch_website'),
    path('staging/<int:pk>/edit/', LeadStagingUpdateView.as_view(), name='lead_staging_edit'),
    path('staging/<int:pk>/import/', LeadStagingImportView.as_view(), name='lead_staging_import'),
    path('staging/<int:pk>/quick-update/', LeadStagingQuickUpdateView.as_view(), name='lead_staging_quick_update'),
    path('staging/bulk-import/', LeadStagingBulkImportView.as_view(), name='lead_staging_bulk_import'),
    path('help/', CrmHelpView.as_view(), name='help'),
    path('api/', include('apps.crm.api.urls', namespace='crm_api')),
]

if SpectacularSwaggerView is not None:
    class CrmSwaggerView(SpectacularSwaggerView):
        schema = None
        permission_classes = [IsAdminUser]

        def get(self, request, *args, **kwargs):
            response = super().get(request, *args, **kwargs)
            if isinstance(response.data, dict) and 'script_url' not in response.data:
                response.data['script_url'] = None
            return response

    class CrmSchemaView(SpectacularAPIView):
        permission_classes = [IsAdminUser]

    class CrmRedocView(SpectacularRedocView):
        permission_classes = [IsAdminUser]

    urlpatterns += [
        path('api/schema/', CrmSchemaView.as_view(urlconf='apps.crm.api.urls'), name='crm-schema'),
        path('api/docs/', CrmSwaggerView.as_view(url_name='crm-schema'), name='crm-swagger'),
        path('api/redoc/', CrmRedocView.as_view(url_name='crm-schema'), name='crm-redoc'),
    ]
