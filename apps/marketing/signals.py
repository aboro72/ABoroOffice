from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.marketing.models import ContentAsset
from apps.workflows.services import run_workflows_for_trigger


@receiver(pre_save, sender=ContentAsset)
def _marketing_store_status(sender, instance, **kwargs):
    if not instance.pk:
        return
    old = ContentAsset.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
    instance._old_status = old


@receiver(post_save, sender=ContentAsset)
def _marketing_asset_saved(sender, instance, created, **kwargs):
    if created:
        return
    if hasattr(instance, '_old_status') and instance._old_status != instance.status:
        try:
            run_workflows_for_trigger('marketing_asset_status', context={'asset_id': instance.id, 'status': instance.status})
        except Exception:
            pass
    if hasattr(instance, '_old_status'):
        delattr(instance, '_old_status')
