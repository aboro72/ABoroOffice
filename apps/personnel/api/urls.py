from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeachingSkillViewSet,
    InstructorViewSet,
    DepartmentViewSet,
    EmployeeViewSet,
    TimeEntryViewSet,
)

app_name = 'personnel_api'

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r'skills', TeachingSkillViewSet, basename='skills')
router.register(r'external-employees', InstructorViewSet, basename='external-employees')
router.register(r'departments', DepartmentViewSet, basename='departments')
router.register(r'employees', EmployeeViewSet, basename='employees')
router.register(r'time-entries', TimeEntryViewSet, basename='time-entries')

urlpatterns = [
    path('', include(router.urls)),
]
