from decimal import Decimal
from django.db import models
from django.utils import timezone


class Account(models.Model):
    TYPES = [
        ('asset', 'Aktiv'),
        ('liability', 'Passiv'),
        ('equity', 'Eigenkapital'),
        ('income', 'Ertrag'),
        ('expense', 'Aufwand'),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=TYPES, default='expense')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} {self.name}"


class CostCenter(models.Model):
    TYPES = [
        ('main', 'Hauptkostenstelle'),
        ('support', 'Hilfskostenstelle'),
        ('other', 'Nebenkostenstelle'),
        ('project', 'Projekt'),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    cost_center_type = models.CharField(max_length=20, choices=TYPES, default='main')
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} {self.name}"


class CostType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} {self.name}"


class BusinessPartner(models.Model):
    TYPES = [
        ('debtor', 'Debitor'),
        ('creditor', 'Kreditor'),
        ('both', 'Beides'),
    ]

    partner_type = models.CharField(max_length=20, choices=TYPES, default='debtor')
    partner_number = models.CharField(max_length=50, blank=True)
    name = models.CharField(max_length=200)
    vat_id = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_partner_type_display()})"


class JournalEntry(models.Model):
    date = models.DateField(default=timezone.now)
    reference = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=255, blank=True)
    total_debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    erp_invoice = models.ForeignKey('erp.Invoice', on_delete=models.SET_NULL, null=True, blank=True)
    erp_salesorder = models.ForeignKey('erp.SalesOrder', on_delete=models.SET_NULL, null=True, blank=True)
    erp_stockreceipt = models.ForeignKey('erp.StockReceipt', on_delete=models.SET_NULL, null=True, blank=True)
    contract = models.ForeignKey('contracts.Contract', on_delete=models.SET_NULL, null=True, blank=True)
    employee = models.ForeignKey('personnel.Employee', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def recalc_totals(self):
        debit = Decimal('0.00')
        credit = Decimal('0.00')
        for line in self.lines.all():
            debit += Decimal(str(line.debit or 0))
            credit += Decimal(str(line.credit or 0))
        self.total_debit = debit
        self.total_credit = credit
        self.save(update_fields=['total_debit', 'total_credit'])

    def __str__(self):
        return f"JE-{self.id} {self.date}"


class JournalLine(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    cost_type = models.ForeignKey(CostType, on_delete=models.SET_NULL, null=True, blank=True)
    partner = models.ForeignKey(BusinessPartner, on_delete=models.SET_NULL, null=True, blank=True)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.entry.recalc_totals()

    def delete(self, *args, **kwargs):
        entry = self.entry
        super().delete(*args, **kwargs)
        entry.recalc_totals()


class FibuSettings(models.Model):
    auto_posting_enabled = models.BooleanField(default=True)
    receivable_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fibu_receivable_accounts',
    )
    revenue_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fibu_revenue_accounts',
    )
    vat_output_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fibu_vat_output_accounts',
    )
    inventory_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fibu_inventory_accounts',
    )
    payable_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fibu_payable_accounts',
    )
    expense_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fibu_expense_accounts',
    )
    default_cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fibu_default_centers',
    )

    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj
