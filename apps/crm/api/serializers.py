from rest_framework import serializers
from apps.crm.models import Account, Lead, Opportunity, Activity, Note


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            'id',
            'name',
            'industry',
            'website',
            'phone',
            'email',
            'address',
            'status',
            'owner',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            'id',
            'name',
            'company',
            'email',
            'phone',
            'website',
            'address',
            'source',
            'status',
            'score',
            'rule_score',
            'ai_score',
            'score_reason',
            'score_updated_at',
            'ai_summary',
            'ai_next_steps',
            'ai_followup_subject',
            'ai_followup_body',
            'ai_last_question',
            'ai_last_answer',
            'ai_last_analyzed',
            'ai_status',
            'ai_error',
            'owner',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'score',
            'rule_score',
            'ai_score',
            'score_reason',
            'score_updated_at',
            'ai_summary',
            'ai_next_steps',
            'ai_followup_subject',
            'ai_followup_body',
            'ai_last_question',
            'ai_last_answer',
            'ai_last_analyzed',
            'ai_status',
            'ai_error',
            'created_at',
            'updated_at',
        ]


class OpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Opportunity
        fields = [
            'id',
            'account',
            'name',
            'stage',
            'amount',
            'close_date',
            'owner',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = [
            'id',
            'account',
            'contact',
            'lead',
            'opportunity',
            'activity_type',
            'subject',
            'due_date',
            'status',
            'owner',
            'created_at',
        ]
        read_only_fields = ['created_at']


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = [
            'id',
            'account',
            'contact',
            'lead',
            'opportunity',
            'content',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['created_at']
