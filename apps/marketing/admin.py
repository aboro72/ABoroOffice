from django.contrib import admin
from .models import Campaign, ContentAsset, ContentIdea, ContentApproval


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'start_date', 'end_date', 'owner']
    list_filter = ['status']
    search_fields = ['name', 'objective']


@admin.register(ContentAsset)
class ContentAssetAdmin(admin.ModelAdmin):
    list_display = ['title', 'asset_type', 'status', 'campaign', 'scheduled_at']
    list_filter = ['asset_type', 'status']
    search_fields = ['title', 'content']


@admin.register(ContentIdea)
class ContentIdeaAdmin(admin.ModelAdmin):
    list_display = ['title', 'target_audience', 'created_at']
    search_fields = ['title', 'description']


@admin.register(ContentApproval)
class ContentApprovalAdmin(admin.ModelAdmin):
    list_display = ['asset', 'status', 'requested_by', 'reviewed_by', 'created_at']
    list_filter = ['status']
