from rest_framework import serializers
from apps.personnel.models import (
    TeachingSkill,
    Instructor,
    Department,
    Employee,
    TimeEntry,
)


class TeachingSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeachingSkill
        fields = ['id', 'name', 'description']


class InstructorSerializer(serializers.ModelSerializer):
    skills = TeachingSkillSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=TeachingSkill.objects.all(),
        many=True,
        write_only=True,
        source='skills',
        required=False,
    )

    class Meta:
        model = Instructor
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'daily_rate',
            'product',
            'skills',
            'skill_ids',
            'is_active',
            'notes',
            'created_at',
        ]
        read_only_fields = ['created_at']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description']


class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'address',
            'assignment_location',
            'department',
            'department_name',
            'cost_center_code',
            'cost_center_name',
            'employment_type',
            'hourly_rate',
            'monthly_salary',
            'start_date',
            'end_date',
            'is_active',
            'notes',
            'created_at',
        ]
        read_only_fields = ['created_at']


class TimeEntrySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)

    class Meta:
        model = TimeEntry
        fields = [
            'id',
            'employee',
            'employee_name',
            'date',
            'hours',
            'assignment_location',
            'notes',
            'created_at',
        ]
        read_only_fields = ['created_at']
