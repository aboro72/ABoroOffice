from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from apps.personnel.models import (
    TeachingSkill,
    Instructor,
    Department,
    Employee,
    TimeEntry,
)
from .serializers import (
    TeachingSkillSerializer,
    InstructorSerializer,
    DepartmentSerializer,
    EmployeeSerializer,
    TimeEntrySerializer,
)


class BasePersonnelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ['-id']


class TeachingSkillViewSet(BasePersonnelViewSet):
    queryset = TeachingSkill.objects.all()
    serializer_class = TeachingSkillSerializer
    search_fields = ['name']
    ordering_fields = ['name']


class InstructorViewSet(BasePersonnelViewSet):
    queryset = Instructor.objects.prefetch_related('skills').all()
    serializer_class = InstructorSerializer
    search_fields = ['name', 'email']
    ordering_fields = ['name', 'created_at', 'daily_rate']
    filterset_fields = ['is_active']

    def get_queryset(self):
        qs = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        return qs


class DepartmentViewSet(BasePersonnelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    search_fields = ['name']
    ordering_fields = ['name']


class EmployeeViewSet(BasePersonnelViewSet):
    queryset = Employee.objects.select_related('department').all()
    serializer_class = EmployeeSerializer
    search_fields = ['name', 'email', 'cost_center_code']
    ordering_fields = ['name', 'created_at', 'start_date']

    def get_queryset(self):
        qs = super().get_queryset()
        department = self.request.query_params.get('department')
        is_active = self.request.query_params.get('is_active')
        employment_type = self.request.query_params.get('employment_type')
        if department:
            qs = qs.filter(department_id=department)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        if employment_type:
            qs = qs.filter(employment_type=employment_type)
        return qs


class TimeEntryViewSet(BasePersonnelViewSet):
    queryset = TimeEntry.objects.select_related('employee', 'employee__department').all()
    serializer_class = TimeEntrySerializer
    search_fields = ['assignment_location', 'notes']
    ordering_fields = ['date', 'created_at', 'hours']

    def get_queryset(self):
        qs = super().get_queryset()
        employee = self.request.query_params.get('employee')
        department = self.request.query_params.get('department')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        month = self.request.query_params.get('month')  # YYYY-MM format
        if employee:
            qs = qs.filter(employee_id=employee)
        if department:
            qs = qs.filter(employee__department_id=department)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if month:
            qs = qs.filter(date__startswith=month)
        return qs
