from rest_framework import serializers
from apps.contracts.models import Contract, ContractVersion


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = [
            'id',
            'title',
            'counterparty',
            'status',
            'start_date',
            'end_date',
            'renewal_date',
            'value_eur',
            'owner',
            'file',
            'notes',
            'ai_summary',
            'ai_risks',
            'ai_checklist',
            'ai_key_dates',
            'ai_last_analyzed',
            'ai_status',
            'ai_error',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'ai_summary',
            'ai_risks',
            'ai_checklist',
            'ai_key_dates',
            'ai_last_analyzed',
            'ai_status',
            'ai_error',
            'created_at',
            'updated_at',
        ]


class ContractVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractVersion
        fields = [
            'id',
            'contract',
            'label',
            'file',
            'summary',
            'uploaded_at',
        ]
        read_only_fields = ['uploaded_at']
