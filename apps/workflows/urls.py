from django.urls import path
from .views import WorkflowHomeView, WorkflowHelpView, WorkflowListView, WorkflowCreateView, WorkflowDetailView

app_name = 'workflows'

urlpatterns = [
    path('', WorkflowHomeView.as_view(), name='home'),
    path('help/', WorkflowHelpView.as_view(), name='help'),
    path('workflows/', WorkflowListView.as_view(), name='workflow_list'),
    path('workflows/create/', WorkflowCreateView.as_view(), name='workflow_create'),
    path('workflows/<int:pk>/', WorkflowDetailView.as_view(), name='workflow_detail'),
]
