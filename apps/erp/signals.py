from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from apps.helpdesk.helpdesk_apps.admin_panel.models import AuditLog, SystemSettings
from apps.erp.models import Quote, SalesOrder, Invoice, OrderConfirmation, DunningNotice
from apps.erp.services.invoice_mail import send_invoice_email
from django.utils import timezone
from apps.workflows.services import run_workflows_for_action, run_workflows_for_trigger


@receiver(pre_save, sender=SalesOrder)
def _erp_store_old_status(sender, instance, **kwargs):
    if not instance.pk:
        return
    old = SalesOrder.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
    instance._old_status = old


def _log(action, instance, old_values=None):
    AuditLog.objects.create(
        action=action,
        user=None,
        content_type=f"erp.{instance.__class__.__name__}",
        object_id=instance.pk,
        description=f"{action} {instance.__class__.__name__}",
        old_values=old_values or {},
        new_values=model_to_dict(instance),
    )


@receiver(post_save, sender=Quote)
@receiver(post_save, sender=SalesOrder)
@receiver(post_save, sender=Invoice)
@receiver(post_save, sender=OrderConfirmation)
@receiver(post_save, sender=DunningNotice)
def erp_saved(sender, instance, created, **kwargs):
    _log('created' if created else 'updated', instance)
    if isinstance(instance, Invoice) and instance.status == 'issued':
        if instance.email_sent_at is None:
            if send_invoice_email(instance):
                instance.email_sent_at = timezone.now()
                instance.save(update_fields=['email_sent_at'])
        try:
            run_workflows_for_action('erp_invoice_email', context={'invoice_id': instance.id}, trigger='invoice_issued')
        except Exception:
            pass

    if isinstance(instance, SalesOrder):
        if instance.status in ('confirmed', 'invoiced') and not instance.invoices.exists():
            settings_obj = SystemSettings.get_settings()
            invoice = Invoice.objects.create(
                order=instance,
                status='issued',
                issue_date=timezone.now().date(),
                due_date=timezone.now().date() + timezone.timedelta(days=settings_obj.invoice_payment_days),
                tax_rate=instance.tax_rate,
                net_amount=instance.net_amount,
                tax_amount=instance.tax_amount,
                total_amount=instance.total_amount,
            )
            try:
                if settings_obj.invoice_auto_send:
                    if send_invoice_email(invoice):
                        invoice.email_sent_at = timezone.now()
                        invoice.save(update_fields=['email_sent_at'])
            except Exception:
                pass
        if hasattr(instance, '_old_status') and instance._old_status != instance.status:
            try:
                run_workflows_for_trigger('erp_order_status', context={'order_id': instance.id, 'status': instance.status})
            except Exception:
                pass

    if isinstance(instance, DunningNotice) and created:
        try:
            run_workflows_for_action('erp_dunning_email', context={'dunning_id': instance.id}, trigger='dunning_created')
        except Exception:
            pass


@receiver(post_save, sender=SalesOrder)
def _erp_clear_old_status(sender, instance, **kwargs):
    if hasattr(instance, '_old_status'):
        delattr(instance, '_old_status')


@receiver(post_delete, sender=Quote)
@receiver(post_delete, sender=SalesOrder)
@receiver(post_delete, sender=Invoice)
@receiver(post_delete, sender=OrderConfirmation)
@receiver(post_delete, sender=DunningNotice)
def erp_deleted(sender, instance, **kwargs):
    _log('deleted', instance)
