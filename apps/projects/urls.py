from django.urls import path
from .views import ProjectsHomeView, ProjectsHelpView, ProjectListView, ProjectCreateView, ProjectDetailView, TaskListView, TaskCreateView, TaskDetailView, KanbanView, GanttView, TaskStatusUpdateView, GanttExportView

app_name = 'projects'

urlpatterns = [
    path('', ProjectsHomeView.as_view(), name='home'),
    path('help/', ProjectsHelpView.as_view(), name='help'),
    path('projects/', ProjectListView.as_view(), name='project_list'),
    path('projects/create/', ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
    path('kanban/', KanbanView.as_view(), name='kanban'),
    path('gantt/', GanttView.as_view(), name='gantt'),
    path('tasks/', TaskListView.as_view(), name='task_list'),
    path('tasks/create/', TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/status/', TaskStatusUpdateView.as_view(), name='task_status'),
    path('gantt/export/', GanttExportView.as_view(), name='gantt_export'),
]
