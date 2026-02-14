from django.views.generic import ListView, CreateView, UpdateView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from .models import Instructor, TeachingSkill, Department, Employee, TimeEntry
from .forms import InstructorForm, TeachingSkillForm, DepartmentForm, EmployeeForm, TimeEntryForm


class PersonnelBaseView(LoginRequiredMixin):
    login_url = '/cloudstorage/accounts/login/'


class PersonnelHelpView(LoginRequiredMixin, TemplateView):
    template_name = 'personnel/help.html'


class InstructorListView(PersonnelBaseView, ListView):
    model = Instructor
    template_name = 'personnel/instructor_list.html'
    context_object_name = 'instructors'

    def get_queryset(self):
        return Instructor.objects.all().order_by('name')


class InstructorCreateView(PersonnelBaseView, CreateView):
    model = Instructor
    form_class = InstructorForm
    template_name = 'personnel/instructor_form.html'
    success_url = '/personnel/instructors/'


class InstructorUpdateView(PersonnelBaseView, UpdateView):
    model = Instructor
    form_class = InstructorForm
    template_name = 'personnel/instructor_form.html'
    success_url = '/personnel/instructors/'


class TeachingSkillListView(PersonnelBaseView, ListView):
    model = TeachingSkill
    template_name = 'personnel/skill_list.html'
    context_object_name = 'skills'

    def get_queryset(self):
        return TeachingSkill.objects.all().order_by('name')


class TeachingSkillCreateView(PersonnelBaseView, CreateView):
    model = TeachingSkill
    form_class = TeachingSkillForm
    template_name = 'personnel/form.html'
    success_url = '/personnel/skills/'


class TeachingSkillUpdateView(PersonnelBaseView, UpdateView):
    model = TeachingSkill
    form_class = TeachingSkillForm
    template_name = 'personnel/form.html'
    success_url = '/personnel/skills/'


class DepartmentListView(PersonnelBaseView, ListView):
    model = Department
    template_name = 'personnel/department_list.html'
    context_object_name = 'departments'

    def get_queryset(self):
        return Department.objects.all().order_by('name')


class DepartmentCreateView(PersonnelBaseView, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'personnel/form.html'
    success_url = '/personnel/departments/'


class DepartmentUpdateView(PersonnelBaseView, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'personnel/form.html'
    success_url = '/personnel/departments/'


class EmployeeListView(PersonnelBaseView, ListView):
    model = Employee
    template_name = 'personnel/employee_list.html'
    context_object_name = 'employees'

    def get_queryset(self):
        qs = Employee.objects.select_related('department').all().order_by('name')
        dept = self.request.GET.get('department')
        if dept:
            qs = qs.filter(department_id=dept)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all().order_by('name')
        context['selected_department'] = self.request.GET.get('department', '')
        return context


class EmployeeCreateView(PersonnelBaseView, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'personnel/form.html'
    success_url = '/personnel/employees/'


class EmployeeUpdateView(PersonnelBaseView, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'personnel/form.html'
    success_url = '/personnel/employees/'


class TimeEntryListView(PersonnelBaseView, ListView):
    model = TimeEntry
    template_name = 'personnel/timeentry_list.html'
    context_object_name = 'entries'

    def get_queryset(self):
        qs = TimeEntry.objects.select_related('employee', 'employee__department').order_by('-date')
        dept = self.request.GET.get('department')
        month = self.request.GET.get('month')
        if dept:
            qs = qs.filter(employee__department_id=dept)
        if month:
            qs = qs.filter(date__startswith=month)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all().order_by('name')
        context['selected_department'] = self.request.GET.get('department', '')
        context['selected_month'] = self.request.GET.get('month', '')
        # Monthly totals per employee
        month = context['selected_month']
        if month:
            monthly = (
                TimeEntry.objects
                .select_related('employee')
                .filter(date__startswith=month)
                .values('employee__id', 'employee__name')
                .annotate(total_hours=models.Sum('hours'))
                .order_by('employee__name')
            )
        else:
            monthly = []
        context['monthly_summary'] = monthly
        return context


class TimeEntryCreateView(PersonnelBaseView, CreateView):
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = 'personnel/form.html'
    success_url = '/personnel/time-entries/'


class TimeEntryUpdateView(PersonnelBaseView, UpdateView):
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = 'personnel/form.html'
    success_url = '/personnel/time-entries/'


class PayrollExportView(PersonnelBaseView, View):
    def get(self, request):
        month = request.GET.get('month', '')
        dept = request.GET.get('department', '')
        qs = TimeEntry.objects.select_related('employee', 'employee__department')
        if month:
            qs = qs.filter(date__startswith=month)
        if dept:
            qs = qs.filter(employee__department_id=dept)
        totals = {}
        for entry in qs:
            emp = entry.employee
            if emp.id not in totals:
                totals[emp.id] = {
                    'name': emp.name,
                    'department': emp.department.name if emp.department else '',
                    'cost_center_code': emp.cost_center_code or '',
                    'cost_center_name': emp.cost_center_name or '',
                    'hours': 0,
                    'hourly_rate': emp.hourly_rate,
                    'monthly_salary': emp.monthly_salary,
                    'locations': set(),
                }
            totals[emp.id]['hours'] += float(entry.hours or 0)
            if entry.assignment_location:
                totals[emp.id]['locations'].add(entry.assignment_location)
        lines = []
        lines.append('Name,Abteilung,Kostenstelle_Code,Kostenstelle_Name,Einsatzort,Stunden,Stundensatz,Monatsgehalt,Netto,Brutto')
        for _, data in totals.items():
            hours = data['hours']
            hourly = float(data['hourly_rate'] or 0)
            monthly = float(data['monthly_salary'] or 0)
            amount = monthly if monthly > 0 else hours * hourly
            locations = data['locations']
            if not locations:
                location = ''
            elif len(locations) == 1:
                location = list(locations)[0]
            else:
                location = 'MULTI'
            net = amount
            gross = amount
            lines.append(
                f"{data['name']},{data['department']},{data['cost_center_code']},{data['cost_center_name']},"
                f"{location},{hours:.2f},{hourly:.2f},{monthly:.2f},{net:.2f},{gross:.2f}"
            )
        content = "\n".join(lines)
        response = HttpResponse(content, content_type='text/csv')
        filename = f"payroll_{month or 'all'}.csv"
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
