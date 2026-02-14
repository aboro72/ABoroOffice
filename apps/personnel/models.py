from django.db import models
from apps.erp.models import Product


class TeachingSkill(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Instructor(models.Model):
    """Externe Mitarbeiter (z.B. Dozenten, Trainer)"""
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    daily_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    skills = models.ManyToManyField(TeachingSkill, blank=True, related_name='instructors')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Externer Mitarbeiter'
        verbose_name_plural = 'Externe Mitarbeiter'


class Department(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Employee(models.Model):
    EMPLOYMENT_TYPES = [
        ('full_time', 'Vollzeit'),
        ('part_time', 'Teilzeit'),
        ('contract', 'Freelancer'),
        ('temp', 'Befristet'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    assignment_location = models.CharField(max_length=200, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    cost_center_code = models.CharField(max_length=50, blank=True)
    cost_center_name = models.CharField(max_length=200, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='full_time')
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TimeEntry(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='time_entries')
    date = models.DateField()
    hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    assignment_location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} {self.date}"
