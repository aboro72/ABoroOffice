from django import forms
from .models import Instructor, TeachingSkill, Department, Employee, TimeEntry


class BasePersonnelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault('class', 'form-select')
            else:
                widget.attrs.setdefault('class', 'form-control')


class TeachingSkillForm(BasePersonnelForm):
    class Meta:
        model = TeachingSkill
        fields = ['name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class InstructorForm(BasePersonnelForm):
    class Meta:
        model = Instructor
        fields = ['name', 'email', 'phone', 'daily_rate', 'product', 'skills', 'is_active', 'notes']
        widgets = {
            'skills': forms.SelectMultiple(attrs={'size': 6}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class DepartmentForm(BasePersonnelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class EmployeeForm(BasePersonnelForm):
    class Meta:
        model = Employee
        fields = [
            'name',
            'email',
            'phone',
            'address',
            'assignment_location',
            'department',
            'cost_center_code',
            'cost_center_name',
            'employment_type',
            'hourly_rate',
            'monthly_salary',
            'start_date',
            'end_date',
            'is_active',
            'notes',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class TimeEntryForm(BasePersonnelForm):
    class Meta:
        model = TimeEntry
        fields = ['employee', 'date', 'hours', 'assignment_location', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
