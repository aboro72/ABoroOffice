from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.crm.models import Lead, Opportunity
from apps.workflows.services import run_workflows_for_trigger


@receiver(pre_save, sender=Lead)
def _crm_store_lead_status(sender, instance, **kwargs):
    if not instance.pk:
        return
    old = Lead.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
    instance._old_status = old


@receiver(post_save, sender=Lead)
def _crm_lead_saved(sender, instance, created, **kwargs):
    if created:
        return
    if hasattr(instance, '_old_status') and instance._old_status != instance.status:
        try:
            run_workflows_for_trigger('crm_lead_status', context={'lead_id': instance.id, 'status': instance.status})
        except Exception:
            pass
    if hasattr(instance, '_old_status'):
        delattr(instance, '_old_status')


@receiver(pre_save, sender=Opportunity)
def _crm_store_opp_stage(sender, instance, **kwargs):
    if not instance.pk:
        return
    old = Opportunity.objects.filter(pk=instance.pk).values_list('stage', flat=True).first()
    instance._old_stage = old


@receiver(post_save, sender=Opportunity)
def _crm_opp_saved(sender, instance, created, **kwargs):
    if created:
        return
    if hasattr(instance, '_old_stage') and instance._old_stage != instance.stage:
        try:
            run_workflows_for_trigger('crm_opportunity_stage', context={'opportunity_id': instance.id, 'stage': instance.stage})
        except Exception:
            pass
    if hasattr(instance, '_old_stage'):
        delattr(instance, '_old_stage')
