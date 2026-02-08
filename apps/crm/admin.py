from django.contrib import admin
from .models import (
    Account,
    Contact,
    Lead,
    Opportunity,
    Activity,
    Note,
    EmailTemplate,
    EmailLog,
    LeadSourceProfile,
    LeadImportJob,
    LeadStaging,
    SourceRequestLog,
)
from .services.lead_sources import run_import_for_profile


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'industry', 'owner', 'updated_at')
    search_fields = ('name', 'industry', 'email', 'phone')
    list_filter = ('status', 'industry')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'account', 'email', 'phone', 'owner')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    list_filter = ('account',)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'source', 'rule_score', 'ai_score', 'score', 'owner', 'updated_at')
    search_fields = ('name', 'company', 'email', 'phone')
    list_filter = ('status', 'source')


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'stage', 'amount', 'close_date', 'owner')
    search_fields = ('name', 'account__name')
    list_filter = ('stage',)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('subject', 'activity_type', 'status', 'due_date', 'owner')
    search_fields = ('subject',)
    list_filter = ('activity_type', 'status')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by', 'created_at')
    search_fields = ('content',)


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'updated_at')
    search_fields = ('name', 'slug', 'subject')
    list_filter = ('is_active',)


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('to_email', 'subject', 'status', 'sent_at', 'created_by')
    search_fields = ('to_email', 'subject')
    list_filter = ('status',)


@admin.register(LeadSourceProfile)
class LeadSourceProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'source', 'keywords', 'keyword_mode', 'schedule', 'enabled', 'last_run_at')
    list_filter = ('source', 'schedule', 'enabled')
    search_fields = ('name', 'keywords', 'ort')
    actions = ['run_import_now']

    def run_import_now(self, request, queryset):
        for profile in queryset:
            run_import_for_profile(profile)
        self.message_user(request, f"Import gestartet für {queryset.count()} Profile.")


@admin.register(LeadImportJob)
class LeadImportJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'status', 'imported_count', 'skipped_count', 'started_at', 'finished_at')
    list_filter = ('status', 'profile')
    search_fields = ('profile__name',)


@admin.register(LeadStaging)
class LeadStagingAdmin(admin.ModelAdmin):
    list_display = ('company', 'email', 'phone', 'status', 'profile', 'created_at')
    list_filter = ('status', 'profile')
    search_fields = ('company', 'email', 'phone')


@admin.register(SourceRequestLog)
class SourceRequestLogAdmin(admin.ModelAdmin):
    list_display = ('source', 'requested_at')
    list_filter = ('source',)
