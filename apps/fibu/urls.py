from django.urls import path, include
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
except Exception:
    SpectacularAPIView = SpectacularSwaggerView = SpectacularRedocView = None
from .views import (
    AccountListView,
    AccountCreateView,
    AccountImportView,
    CostCenterListView,
    CostCenterCreateView,
    CostTypeListView,
    CostTypeCreateView,
    BusinessPartnerListView,
    BusinessPartnerCreateView,
    JournalEntryListView,
    JournalEntryCreateView,
    JournalEntryDetailView,
    FibuHelpView,
    FibuSettingsView,
)

app_name = 'fibu'

urlpatterns = [
    path('accounts/', AccountListView.as_view(), name='accounts'),
    path('accounts/create/', AccountCreateView.as_view(), name='account_create'),
    path('accounts/import/', AccountImportView.as_view(), name='account_import'),
    path('cost-centers/', CostCenterListView.as_view(), name='cost_centers'),
    path('cost-centers/create/', CostCenterCreateView.as_view(), name='cost_center_create'),
    path('cost-types/', CostTypeListView.as_view(), name='cost_types'),
    path('cost-types/create/', CostTypeCreateView.as_view(), name='cost_type_create'),
    path('partners/', BusinessPartnerListView.as_view(), name='partners'),
    path('partners/create/', BusinessPartnerCreateView.as_view(), name='partner_create'),
    path('journal/', JournalEntryListView.as_view(), name='journal'),
    path('journal/create/', JournalEntryCreateView.as_view(), name='journal_create'),
    path('journal/<int:pk>/', JournalEntryDetailView.as_view(), name='journal_detail'),
    path('help/', FibuHelpView.as_view(), name='help'),
    path('settings/', FibuSettingsView.as_view(), name='settings'),
    path('api/', include('apps.fibu.api.urls')),
]

if SpectacularSwaggerView is not None:
    class FibuSwaggerView(SpectacularSwaggerView):
        schema = None

    class FibuRedocView(SpectacularRedocView):
        schema = None

    class FibuSchemaView(SpectacularAPIView):
        api_version = 'v1'

    urlpatterns += [
        path('api/schema/', FibuSchemaView.as_view(urlconf='apps.fibu.api.urls'), name='fibu-schema'),
        path('api/docs/', FibuSwaggerView.as_view(url_name='fibu-schema'), name='fibu-swagger'),
        path('api/redoc/', FibuRedocView.as_view(url_name='fibu-schema'), name='fibu-redoc'),
    ]
