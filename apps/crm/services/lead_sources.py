from datetime import timedelta
from django.utils import timezone
from apps.crm.models import LeadSourceProfile
from apps.crm.services import handelsregister
from apps.crm.services.fallbacks import run_fallback_import
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings


SOURCE_HANDLERS = {
    handelsregister.SOURCE_KEY: handelsregister.import_profile,
}


def run_import_for_profile(profile: LeadSourceProfile):
    handler = SOURCE_HANDLERS.get(profile.source)
    if not handler:
        raise RuntimeError(f"No handler for source: {profile.source}")
    job = handler(profile, max_count=profile.max_per_run)
    settings_obj = SystemSettings.get_settings()
    if settings_obj.crm_fallback_enabled and job.imported_count == 0:
        return run_fallback_import(profile, max_count=profile.max_per_run)
    return job


def run_scheduled_imports():
    now = timezone.now()
    profiles = LeadSourceProfile.objects.filter(enabled=True).exclude(schedule='manual')
    for profile in profiles:
        if profile.last_run_at:
            delta = now - profile.last_run_at
        else:
            delta = None
        if profile.schedule == 'hourly' and (delta is None or delta >= timedelta(hours=1)):
            run_import_for_profile(profile)
        if profile.schedule == 'daily' and (delta is None or delta >= timedelta(days=1)):
            run_import_for_profile(profile)
        if profile.schedule == 'weekly' and (delta is None or delta >= timedelta(days=7)):
            run_import_for_profile(profile)
