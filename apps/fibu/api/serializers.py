from rest_framework import serializers
from apps.fibu.models import Account, CostCenter, CostType, BusinessPartner, JournalEntry, JournalLine


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class CostCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = '__all__'


class CostTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostType
        fields = '__all__'


class BusinessPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessPartner
        fields = '__all__'


class JournalLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalLine
        fields = '__all__'


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True, read_only=True)

    class Meta:
        model = JournalEntry
        fields = '__all__'
