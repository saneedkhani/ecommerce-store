from rest_framework import serializers
from .models import Payment
from .services import STAFF_STATUSES


class PaymentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Payment
        fields = ['id', 'order', 'user', 'bank_reference', 'proof_screenshot', 'status', 'created_at']
        read_only_fields = ['order', 'status', 'created_at']

    def validate(self, attrs):
        if not attrs.get('bank_reference') and not attrs.get('proof_screenshot'):
            raise serializers.ValidationError('Provide a bank reference, a screenshot, or both.')
        return attrs


class PaymentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=STAFF_STATUSES)
