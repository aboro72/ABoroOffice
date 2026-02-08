from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from apps.helpdesk.helpdesk_apps.admin_panel.models import AuditLog
from apps.fibu.models import Account, CostCenter, CostType, BusinessPartner, JournalEntry, JournalLine


def _log(action, instance, old_values=None):
    AuditLog.objects.create(
        action=action,
        user=None,
        content_type=f"fibu.{instance.__class__.__name__}",
        object_id=instance.pk,
        description=f"{action} {instance.__class__.__name__}",
        old_values=old_values or {},
        new_values=model_to_dict(instance),
    )


@receiver(post_save, sender=Account)
@receiver(post_save, sender=CostCenter)
@receiver(post_save, sender=CostType)
@receiver(post_save, sender=BusinessPartner)
@receiver(post_save, sender=JournalEntry)
@receiver(post_save, sender=JournalLine)
def fibu_saved(sender, instance, created, **kwargs):
    _log('created' if created else 'updated', instance)


@receiver(post_delete, sender=Account)
@receiver(post_delete, sender=CostCenter)
@receiver(post_delete, sender=CostType)
@receiver(post_delete, sender=BusinessPartner)
@receiver(post_delete, sender=JournalEntry)
@receiver(post_delete, sender=JournalLine)
def fibu_deleted(sender, instance, **kwargs):
    _log('deleted', instance)
