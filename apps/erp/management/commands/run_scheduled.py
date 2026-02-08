from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings
from apps.erp.models import Invoice
from apps.erp.services.dunning_auto import run_dunning_cycle
from apps.erp.services.invoice_mail import send_invoice_email
from apps.helpdesk.helpdesk_apps.admin_panel.models import EmailLog


class Command(BaseCommand):
    help = 'Run scheduled ERP tasks (dunning + invoice emails). Use via cron/Task Scheduler.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Run regardless of scheduler time window.')

    def _should_run(self, settings_obj: SystemSettings, now: timezone.datetime, force: bool) -> bool:
        if force:
            return True
        if not settings_obj.scheduler_enabled:
            return False
        last_run = settings_obj.scheduler_last_run
        if settings_obj.scheduler_mode == 'interval':
            minutes = max(5, int(settings_obj.scheduler_interval_minutes or 60))
            if not last_run:
                return True
            return now - last_run >= timedelta(minutes=minutes)

        # daily mode
        target = settings_obj.scheduler_daily_time
        if not target:
            return False
        window_start = now.replace(hour=target.hour, minute=target.minute, second=0, microsecond=0)
        window_end = window_start + timedelta(minutes=10)
        if not (window_start <= now <= window_end):
            return False
        if not last_run:
            return True
        return last_run.date() < now.date()

    def handle(self, *args, **options):
        settings_obj = SystemSettings.get_settings()
        now = timezone.now()
        if not self._should_run(settings_obj, now, options.get('force', False)):
            self.stdout.write(self.style.WARNING("Scheduler window not active; skipping. Use --force to run."))
            return

        if settings_obj.email_log_auto_archive_days and settings_obj.email_log_auto_archive_days > 0:
            cutoff = now - timedelta(days=int(settings_obj.email_log_auto_archive_days))
            EmailLog.objects.filter(archived=False, created_at__lt=cutoff).update(archived=True)

        result = run_dunning_cycle()
        self.stdout.write(self.style.SUCCESS(f"Dunning cycle done: {result}"))

        sent = 0
        if settings_obj.invoice_auto_send:
            pending = Invoice.objects.filter(status='issued', email_sent_at__isnull=True)
            for inv in pending:
                if send_invoice_email(inv):
                    inv.email_sent_at = timezone.now()
                    inv.save(update_fields=['email_sent_at'])
                    sent += 1
        self.stdout.write(self.style.SUCCESS(f"Invoice auto-send done: sent={sent}"))

        settings_obj.scheduler_last_run = now
        settings_obj.save(update_fields=['scheduler_last_run'])
