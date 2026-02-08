from django.utils import timezone
from django.db import models
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
from apps.erp.models import Invoice, DunningNotice
from .dunning import build_letter_text, send_dunning_email, mark_sent


def run_dunning_cycle(auto_send: bool | None = None) -> dict:
    settings_obj = SystemSettings.get_settings()
    if not settings_obj.dunning_enabled:
        return {'created': 0, 'sent': 0}

    today = timezone.now().date()
    levels = [
        (1, settings_obj.dunning_days_level1 or 0),
        (2, settings_obj.dunning_days_level2 or 0),
        (3, settings_obj.dunning_days_level3 or 0),
    ]

    created = 0
    sent = 0

    for level, days in levels:
        if days <= 0:
            continue
        cutoff = today - timezone.timedelta(days=int(days))
        invoices = Invoice.objects.filter(status='issued', due_date__isnull=False, due_date__lte=cutoff)
        for inv in invoices:
            exists = DunningNotice.objects.filter(invoice=inv, level=level).exists()
            if exists:
                continue
            notice = DunningNotice.objects.create(
                invoice=inv,
                level=level,
                status='draft',
                due_date=inv.due_date,
            )
            notice.letter_text = build_letter_text(notice)
            notice.email_subject = f"Mahnung {notice.number}"
            notice.email_body = notice.letter_text
            notice.save(update_fields=['letter_text', 'email_subject', 'email_body'])
            created += 1

            do_send = settings_obj.dunning_auto_send if auto_send is None else auto_send
            if do_send:
                if send_dunning_email(notice):
                    mark_sent(notice)
                    sent += 1

    return {'created': created, 'sent': sent}
