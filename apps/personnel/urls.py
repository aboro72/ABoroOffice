from django.urls import path, include
from .views import (
    InstructorListView,
    InstructorCreateView,
    InstructorUpdateView,
    TeachingSkillListView,
    TeachingSkillCreateView,
    TeachingSkillUpdateView,
    DepartmentListView,
    DepartmentCreateView,
    DepartmentUpdateView,
    EmployeeListView,
    EmployeeCreateView,
    EmployeeUpdateView,
    TimeEntryListView,
    TimeEntryCreateView,
    TimeEntryUpdateView,
    PayrollExportView,
    PersonnelHelpView,
)

app_name = 'personnel'

urlpatterns = [
    path('help/', PersonnelHelpView.as_view(), name='help'),
    path('instructors/', InstructorListView.as_view(), name='instructors'),
    path('instructors/create/', InstructorCreateView.as_view(), name='instructor_create'),
    path('instructors/<int:pk>/edit/', InstructorUpdateView.as_view(), name='instructor_edit'),
    path('skills/', TeachingSkillListView.as_view(), name='skills'),
    path('skills/create/', TeachingSkillCreateView.as_view(), name='skill_create'),
    path('skills/<int:pk>/edit/', TeachingSkillUpdateView.as_view(), name='skill_edit'),
    path('departments/', DepartmentListView.as_view(), name='departments'),
    path('departments/create/', DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', DepartmentUpdateView.as_view(), name='department_edit'),
    path('employees/', EmployeeListView.as_view(), name='employees'),
    path('employees/create/', EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/edit/', EmployeeUpdateView.as_view(), name='employee_edit'),
    path('time-entries/', TimeEntryListView.as_view(), name='time_entries'),
    path('time-entries/create/', TimeEntryCreateView.as_view(), name='time_entry_create'),
    path('time-entries/<int:pk>/edit/', TimeEntryUpdateView.as_view(), name='time_entry_edit'),
    path('payroll/export/', PayrollExportView.as_view(), name='payroll_export'),
    path('api/', include('apps.personnel.api.urls', namespace='personnel_api')),
]
