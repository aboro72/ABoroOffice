from django.contrib import admin
from .models import Contract, ContractVersion


class ContractVersionInline(admin.TabularInline):
    model = ContractVersion
    extra = 0


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('title', 'counterparty', 'status', 'start_date', 'end_date', 'owner')
    list_filter = ('status',)
    search_fields = ('title', 'counterparty')
    inlines = [ContractVersionInline]


@admin.register(ContractVersion)
class ContractVersionAdmin(admin.ModelAdmin):
    list_display = ('contract', 'label', 'uploaded_at')
    search_fields = ('contract__title', 'label')
