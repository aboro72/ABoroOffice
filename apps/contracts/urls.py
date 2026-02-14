from django.urls import path, include
from .views import (
    ContractListView,
    ContractDetailView,
    ContractCreateView,
    ContractUpdateView,
    ContractVersionCreateView,
    ContractAnalyzeView,
    ContractExportAnalysisView,
    ContractsHelpView,
)
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
    from rest_framework.permissions import IsAdminUser
except Exception:
    SpectacularAPIView = SpectacularSwaggerView = SpectacularRedocView = None

app_name = 'contracts'

urlpatterns = [
    path('', ContractListView.as_view(), name='contract_list'),
    path('create/', ContractCreateView.as_view(), name='contract_create'),
    path('<int:pk>/', ContractDetailView.as_view(), name='contract_detail'),
    path('<int:pk>/analyze/', ContractAnalyzeView.as_view(), name='contract_analyze'),
    path('<int:pk>/export-analysis/', ContractExportAnalysisView.as_view(), name='contract_export_analysis'),
    path('<int:pk>/edit/', ContractUpdateView.as_view(), name='contract_edit'),
    path('<int:contract_id>/versions/create/', ContractVersionCreateView.as_view(), name='contract_version_create'),
    path('help/', ContractsHelpView.as_view(), name='help'),
    path('api/', include('apps.contracts.api.urls', namespace='contracts_api')),
]

if SpectacularSwaggerView is not None:
    class ContractsSwaggerView(SpectacularSwaggerView):
        schema = None
        permission_classes = [IsAdminUser]

        def get(self, request, *args, **kwargs):
            response = super().get(request, *args, **kwargs)
            if isinstance(response.data, dict) and 'script_url' not in response.data:
                response.data['script_url'] = None
            return response

    class ContractsSchemaView(SpectacularAPIView):
        permission_classes = [IsAdminUser]

    class ContractsRedocView(SpectacularRedocView):
        permission_classes = [IsAdminUser]

    urlpatterns += [
        path('api/schema/', ContractsSchemaView.as_view(urlconf='apps.contracts.api.urls'), name='contracts-schema'),
        path('api/docs/', ContractsSwaggerView.as_view(url_name='contracts:contracts-schema'), name='contracts-swagger'),
        path('api/redoc/', ContractsRedocView.as_view(url_name='contracts:contracts-schema'), name='contracts-redoc'),
    ]
